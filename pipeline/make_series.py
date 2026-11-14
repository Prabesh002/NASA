"""
Backscatter time series for the point inspector: one small image per NISAR date, same grid for all.

For each date on track 098A (frame 016) the HH backscatter (gamma-0 power) of the corridor and source
boxes is averaged onto one Web Mercator grid of about 50 m ground size (averaging in linear power, which
also reduces speckle), converted to dB and stored as an 8-bit greyscale PNG:
    pixel 0      = no valid data
    pixel 1..255 = dB = DB_MIN + (pixel - 1) * DB_STEP
The browser reads the pixel under a click from each PNG and plots the ten values. Nothing is modelled.

Outputs
  site/public/data/series/hh-<YYYYMMDD>.png and series.json (grid, dates, quantisation, sources)
  data/work/series/hh_stack.npy (float32 dB, dates x rows x cols; used by glacier_wet.py)

Usage: python pipeline/make_series.py
SI disclosure: written with SI assistance (Claude, Anthropic). See docs/SI-USAGE.md.
"""
import datetime, glob, json, math, pathlib, re
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from PIL import Image

TRACK = "098A_016"
RAW = ["data/raw/gcov", "data/raw/gcov_source"]          # first with data at a pixel wins
LON0, LAT0, LON1, LAT1 = 85.09, 27.84, 85.66, 28.43
CELL = 56.7                                              # Web Mercator metres; about 50 m on the ground at 28 N
DB_MIN, DB_STEP = -35.0, 0.15
OUT_SITE = pathlib.Path("site/public/data/series")
OUT_WORK = pathlib.Path("data/work/series")
R = 6378137.0
mx = lambda lon: math.radians(lon) * R
my = lambda lat: math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * R


def load(folder, shape, transform):
    """Mean HH power of one scene folder on the target grid (NaN where invalid)."""
    hh = sorted(glob.glob(f"{folder}/*HHHH*.tif"))
    if not hh:
        return None, None
    hh = hh[0]                                           # duplicate Harmony jobs hold the same data
    mask = hh.replace("HHHH", "mask")
    with rasterio.open(hh) as a, rasterio.open(mask) as m:
        p = a.read(1).astype("float32")
        k = m.read(1)
        p[(k == 0) | (k == 255) | ~np.isfinite(p) | (p <= 0)] = np.nan
        dst = np.full(shape, np.nan, "float32")
        reproject(p, dst, src_transform=a.transform, src_crs=a.crs, dst_transform=transform, dst_crs="EPSG:3857",
                  resampling=Resampling.average, src_nodata=np.nan, dst_nodata=np.nan)
    return dst, pathlib.Path(hh).name


def main():
    x0, x1, y0, y1 = mx(LON0), mx(LON1), my(LAT0), my(LAT1)
    w, h = round((x1 - x0) / CELL), round((y1 - y0) / CELL)
    transform = from_origin(x0, y1, CELL, CELL)
    dates = sorted({re.search(r"\d{4}-\d{2}-\d{2}", f).group(0) for f in glob.glob(f"{RAW[0]}/{TRACK}_*")})
    OUT_SITE.mkdir(parents=True, exist_ok=True); OUT_WORK.mkdir(parents=True, exist_ok=True)
    stack, sources = [], {}
    for d in dates:
        power = np.full((h, w), np.nan, "float32"); sources[d] = []
        for raw in RAW:
            for folder in glob.glob(f"{raw}/{TRACK}_{d}_*"):
                part, name = load(folder, (h, w), transform)
                if part is None:
                    continue
                fill = np.isnan(power) & np.isfinite(part)
                power[fill] = part[fill]; sources[d].append(name)
        db = 10 * np.log10(power)
        q = np.where(np.isfinite(db), np.clip(np.round((db - DB_MIN) / DB_STEP) + 1, 1, 255), 0).astype("uint8")
        Image.fromarray(q, "L").save(OUT_SITE / f"hh-{d.replace('-', '')}.png", optimize=True)
        stack.append(db)
        print(d, f"valid {np.isfinite(db).mean():.1%}", f"median {np.nanmedian(db):.2f} dB", sources[d][0][:40])
    np.save(OUT_WORK / "hh_stack.npy", np.stack(stack))
    meta = {"generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "track": TRACK, "polarisation": "HH",
            "quantity": "gamma-0 backscatter, dB, mean over one grid cell", "crs": "EPSG:3857", "cell_m_mercator": CELL,
            "ground_size_m_approx": 50, "x0": x0, "y1": y1, "width": w, "height": h,
            "bounds_lonlat": [LON0, LAT0, LON1, LAT1], "db_min": DB_MIN, "db_step": DB_STEP, "nodata": 0,
            "dates": dates, "files": [f"hh-{d.replace('-', '')}.png" for d in dates], "event_between": ["2026-08-19", "2026-08-31"],
            "source": "NISAR L2 GCOV PROVISIONAL (CRID P05023), HHHH, via NASA Harmony", "source_files": sources}
    (OUT_SITE / "series.json").write_text(json.dumps(meta, indent=1))
    (OUT_WORK / "grid.json").write_text(json.dumps({"x0": x0, "y1": y1, "cell": CELL, "width": w, "height": h, "dates": dates}))


if __name__ == "__main__":
    main()
