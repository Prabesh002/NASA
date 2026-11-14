"""
Quick-look PNGs for visual sanity checks (not shipped to the site).
  python pipeline/quicklook.py <change_tif> <out_png> [--bbox w s e n] [--scale 2] [--lim 6]
  python pipeline/quicklook.py <power_tif> <out_png> --db [--bbox ...]
Change rasters: blue = backscatter dropped, red = rose, white = little change, grey = no data.
SI disclosure: written with SI assistance (Claude, Anthropic). See docs/SI-USAGE.md.
"""
import argparse
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("tif"); ap.add_argument("png")
ap.add_argument("--bbox", type=float, nargs=4, help="lon/lat w s e n")
ap.add_argument("--scale", type=int, default=2)
ap.add_argument("--lim", type=float, default=6.0)
ap.add_argument("--db", action="store_true", help="input is linear power; show as grey dB image")
a = ap.parse_args()

with rasterio.open(a.tif) as src:
    win = None
    if a.bbox:
        b = transform_bounds("EPSG:4326", src.crs, *a.bbox)
        win = from_bounds(*b, transform=src.transform).round_offsets().round_lengths()
    x = src.read(1, window=win, boundless=True, fill_value=np.nan).astype(np.float32)
x = x[::a.scale, ::a.scale]
ok = np.isfinite(x)
if a.db:
    ok &= x > 0
    d = np.full(x.shape, np.nan, np.float32); d[ok] = 10 * np.log10(x[ok])
    t = np.clip((d + 25) / 25, 0, 1)                      # -25 .. 0 dB
    g = (np.nan_to_num(t) * 255).astype(np.uint8)
    rgb = np.dstack([g, g, g])
else:
    t = np.clip(np.nan_to_num(x) / a.lim, -1, 1)
    r = np.where(t > 0, 1.0, 1 + t * 0.85); g = 1 - np.abs(t) * 0.8; bl = np.where(t < 0, 1.0, 1 - t * 0.85)
    rgb = (np.dstack([r, g, bl]) * 255).astype(np.uint8)
rgb[~ok] = (120, 120, 120)
Image.fromarray(rgb).save(a.png)
print(a.png, rgb.shape)
