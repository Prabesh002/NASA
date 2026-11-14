"""
Turn pipeline rasters into web map tiles (XYZ, 256 px, WebP) for the site.

For each layer in LAYERS:
  1. Reproject the source GeoTIFF(s) (UTM 45N) to Web Mercator on the tile grid of MAXZOOM.
     Several sources are mosaicked: the first source with data at a pixel wins.
  2. Colour it.
       kind="change": dB log-ratio. Blue = backscatter fell, red = rose (ColorBrewer RdBu ends,
                      colour-blind safe). Opacity grows from 0 at |change| = T0 dB to full at T1 dB,
                      so small changes (speckle-level) stay transparent and the basemap shows through.
       kind="sar":    linear power -> dB -> grey, fixed stretch LO..HI dB (same for every date so
                      before/after images are comparable).
  3. Cut tiles for MAXZOOM and build lower zooms by 2x2 averaging (alpha-weighted).
  4. Write <out>/<layer>/{z}/{x}/{y}.webp and <out>/<layer>/meta.json (sources, scale, bounds).

Nothing is invented here: every pixel is a resampled, colour-mapped measurement. No smoothing beyond
the 5x5 boxcar already applied in change_detection.py and the resampling to the tile grid.

Usage: python pipeline/make_tiles.py [--layers a,b] [--out site/public/tiles]
SI disclosure: written with SI assistance (Claude, Anthropic). See docs/SI-USAGE.md.
"""
import argparse
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine
from PIL import Image
from rasterio.warp import Resampling, reproject, transform_bounds

ROOT = Path(__file__).resolve().parent.parent
CH = "data/work/change"
RAWC, RAWS = ROOT / "data/raw/gcov", ROOT / "data/raw/gcov_source"
ORIGIN = math.pi * 6378137.0
T0, T1, FULL = 1.5, 4.0, 6.0          # change: transparent below T0 dB, opaque from T1, colour saturates at FULL
SAR_LO, SAR_HI = -24.0, -2.0          # grey stretch for gamma-0 in dB
BLUE, RED, MID = (33, 102, 172), (178, 24, 43), (247, 247, 247)


def raw(folder_root: Path, name: str, var: str) -> str:
    d = folder_root / name
    hits = sorted(d.glob(f"*frequencyA_{var}_subsetted.tif"), key=lambda q: int(q.name.split("_")[0]))
    return hits[-1].relative_to(ROOT).as_posix() if hits else f"MISSING:{name}:{var}"


def change(track, d1, d2, pol):
    return [f"{CH}/gcov/{track}_{d1}_{d2}_{pol}_logratio_dB.tif",
            f"{CH}/gcov_source/{track}_{d1}_{d2}_{pol}_logratio_dB.tif"]


def sar(track, date, tag, pol):
    n = f"{track}_{date}_{tag}"
    return [raw(RAWC, n, pol), raw(RAWS, n, pol)]


S98 = ["2026-06-20", "2026-07-02", "2026-07-14", "2026-07-26", "2026-08-19", "2026-08-31",
       "2026-09-12", "2026-09-24", "2026-10-06", "2026-10-18"]
LAYERS = {
    # the 12 days that contain the flood, three independent viewing geometries
    "chg-098A-hh": dict(kind="change", src=change("098A_016", "2026-08-19", "2026-08-31", "HHHH"), maxzoom=14),
    "chg-098A-hv": dict(kind="change", src=change("098A_016", "2026-08-19", "2026-08-31", "HVHV"), maxzoom=14),
    "chg-048D-hh": dict(kind="change", src=change("048D_074", "2026-08-16", "2026-08-28", "HHHH")
                        + change("048D_075", "2026-08-16", "2026-08-28", "HHHH"), maxzoom=13),
    "chg-149D-hh": dict(kind="change", src=change("149D_074", "2026-08-23", "2026-09-04", "HHHH"), maxzoom=13),
    # the radar images themselves, before and after
    "sar-098A-0819": dict(kind="sar", src=sar("098A_016", "2026-08-19", "before", "HHHH"), maxzoom=14),
    "sar-098A-0831": dict(kind="sar", src=sar("098A_016", "2026-08-31", "after", "HHHH"), maxzoom=14),
}
# every other 12-day step on track 098A = what ordinary change looks like
for _a, _b in zip(S98, S98[1:]):
    if (_a, _b) not in (("2026-08-19", "2026-08-31"), ("2026-07-26", "2026-08-19")):
        LAYERS[f"base-098A-hh-{_a[5:7]}{_a[8:]}"] = dict(
            kind="change", src=change("098A_016", _a, _b, "HHHH"), maxzoom=13)


def tile_of(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def build(name, cfg, out_root: Path):
    srcs = [ROOT / s for s in cfg["src"] if not s.startswith("MISSING") and (ROOT / s).exists()]
    if not srcs:
        print(f"[{name}] no source rasters yet, skipped")
        return
    z = cfg["maxzoom"]
    w = s = 1e9
    e = n = -1e9
    for p in srcs:
        with rasterio.open(p) as r:
            b = transform_bounds(r.crs, "EPSG:4326", *r.bounds, densify_pts=21)
            w, s, e, n = min(w, b[0]), min(s, b[1]), max(e, b[2]), max(n, b[3])
    x0, y0 = (int(math.floor(v)) for v in tile_of(w, n, z))
    x1, y1 = (int(math.floor(v)) for v in tile_of(e, s, z))
    res = 2 * ORIGIN / (256 * 2 ** z)
    W, H = (x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256
    tf = Affine(res, 0, -ORIGIN + x0 * 256 * res, 0, -res, ORIGIN - y0 * 256 * res)
    mosaic = np.full((H, W), np.nan, np.float32)
    for p in srcs:
        tmp = np.full((H, W), np.nan, np.float32)
        with rasterio.open(p) as r:
            reproject(rasterio.band(r, 1), tmp, dst_transform=tf, dst_crs="EPSG:3857",
                      src_nodata=r.nodata, dst_nodata=np.nan, resampling=Resampling.bilinear)
        fill = np.isnan(mosaic) & np.isfinite(tmp)
        mosaic[fill] = tmp[fill]
        del tmp
    ok = np.isfinite(mosaic)
    rgba = np.zeros((H, W, 4), np.float32)
    if cfg["kind"] == "change":
        v = np.nan_to_num(mosaic)
        t = np.clip(np.abs(v) / FULL, 0, 1)[..., None]
        end = np.where((v < 0)[..., None], np.array(BLUE, np.float32), np.array(RED, np.float32))
        rgba[..., :3] = np.array(MID, np.float32) * (1 - t) + end * t
        rgba[..., 3] = np.clip((np.abs(v) - T0) / (T1 - T0), 0, 1) * ok
        scale = dict(unit="dB", transparent_below_abs=T0, opaque_from_abs=T1, colour_saturates_abs=FULL,
                     negative="blue: backscatter fell", positive="red: backscatter rose")
    else:
        ok &= mosaic > 0
        db = np.full(mosaic.shape, SAR_LO, np.float32)
        db[ok] = 10 * np.log10(mosaic[ok])
        g = np.clip((db - SAR_LO) / (SAR_HI - SAR_LO), 0, 1) * 255
        rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = g
        rgba[..., 3] = ok
        scale = dict(unit="dB (gamma-0)", black=SAR_LO, white=SAR_HI)
    del mosaic
    rgba[..., :3] *= rgba[..., 3:4]            # premultiply
    out = out_root / name
    if out.exists():
        shutil.rmtree(out)
    count, minzoom = 0, 8
    for zz in range(z, minzoom - 1, -1):
        tx0, ty0 = x0 >> (z - zz), y0 >> (z - zz)
        if zz < z:
            # pad to an even tile-aligned grid for this zoom, then average 2x2
            px, py = (x0 >> (z - zz - 1)) & 1, (y0 >> (z - zz - 1)) & 1
            hh, ww = rgba.shape[:2]
            hp, wp = py * 256 + hh, px * 256 + ww
            hp, wp = hp + (-hp) % 512, wp + (-wp) % 512
            pad = np.zeros((hp, wp, 4), np.float32)
            pad[py * 256:py * 256 + hh, px * 256:px * 256 + ww] = rgba
            rgba = pad.reshape(hp // 2, 2, wp // 2, 2, 4).mean(axis=(1, 3))
            del pad
        for j in range(rgba.shape[0] // 256):
            for i in range(rgba.shape[1] // 256):
                t = rgba[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256]
                a = t[..., 3]
                if a.max() < 0.02:
                    continue
                with np.errstate(invalid="ignore", divide="ignore"):
                    rgb = np.where(a[..., None] > 0, t[..., :3] / a[..., None], 0)
                im = np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)
                d = out / str(zz) / str(tx0 + i)
                d.mkdir(parents=True, exist_ok=True)
                Image.fromarray(im, "RGBA").save(d / f"{ty0 + j}.webp", quality=82, method=4)
                count += 1
    meta = dict(layer=name, kind=cfg["kind"], minzoom=minzoom, maxzoom=z, bounds=[w, s, e, n],
                scale=scale, sources=[p.relative_to(ROOT).as_posix() for p in srcs], tiles=count,
                generated_utc=datetime.now(timezone.utc).isoformat(),
                note="Derived from NISAR L2 GCOV (PROVISIONAL, CRID P05023). Processed offline; see pipeline/.")
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    size = sum(f.stat().st_size for f in out.rglob("*.webp")) / 1e6
    print(f"[{name}] {count} tiles, {size:.1f} MB, z{minzoom}-{z}, bounds {[round(v, 4) for v in (w, s, e, n)]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers")
    ap.add_argument("--out", default="site/public/tiles")
    a = ap.parse_args()
    names = a.layers.split(",") if a.layers else list(LAYERS)
    for n in names:
        build(n, LAYERS[n], ROOT / a.out)
    # index of every layer present, read by the site
    metas = [json.loads(m.read_text()) for m in sorted((ROOT / a.out).glob("*/meta.json"))]
    data = ROOT / a.out / ".." / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "layers.json").write_text(json.dumps(dict(layers=metas), indent=1))
    print("layers.json:", [m["layer"] for m in metas])


if __name__ == "__main__":
    main()
