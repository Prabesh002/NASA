"""
Before/after radar backscatter change for each NISAR track over the Rasuwa corridor.

Method: the standard SAR log-ratio, written out explicitly so judges can check it.
  1. Read the before and after GCOV gamma-0 power (HHHH, HVHV) and the mask (spec D-102274 §4.3.3:
     0 = invalid, 1..5 = valid, 255 = fill).
  2. Put the after scene on the before scene's grid (rasterio reproject, average resampling).
     Two tracks change mode between dates (10 m vs 20 m pixels), so this step matters.
  3. Reduce speckle with a boxcar mean (default 5x5 px) on linear power.
  4. Change in dB = 10*log10(after / before), only where both masks are valid.
  5. Write a GeoTIFF of the dB change, plus a JSON of summary statistics.
Pairs are consecutive dates on the same track_frame, so a folder holding a whole time series
(track 098A: Jun 20 .. Oct 18, 2026) yields every 12-day step, including the one spanning the flood.

What this does NOT claim: a backscatter change is not, by itself, proof of "flood damage".
Causes can include debris and sediment, water, vegetation loss, moisture, or geometry effects
(the mask does not flag layover/shadow). Interpretation needs other evidence, and that is stated
in the outputs.

Usage: python pipeline/change_detection.py [--window 5] [--raw data/raw/gcov] [--only 098A_016]
Outputs go to data/work/change/<raw folder name>/.
SI disclosure: written with SI assistance (Claude, Anthropic). See docs/SI-USAGE.md.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "gcov"
WORK = ROOT / "data" / "work" / "change"


def find(folder: Path, var: str) -> Path:
    """One file per variable. A re-run of the fetch can leave an older copy next to the new one
    (Harmony prefixes file names with a job number); we take the newest by that prefix."""
    hits = sorted(folder.glob(f"*frequencyA_{var}_subsetted.tif"), key=lambda q: int(q.name.split("_")[0]))
    if not hits:
        raise FileNotFoundError(f"no {var} file in {folder}")
    return hits[-1]


def boxcar(a: np.ndarray, valid: np.ndarray, w: int) -> np.ndarray:
    """Mean over a w x w window using only valid pixels (integral images, memory-friendly)."""
    a = np.where(valid, a, 0.0).astype(np.float64)
    v = valid.astype(np.float64)
    pad = w // 2

    def wsum(x):
        x = np.pad(x, pad, mode="constant")
        c = x.cumsum(0).cumsum(1)
        c = np.pad(c, ((1, 0), (1, 0)))
        return c[w:, w:] - c[:-w, w:] - c[w:, :-w] + c[:-w, :-w]

    s, n = wsum(a), wsum(v)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = s / n
    out[~valid] = np.nan
    return out.astype(np.float32)


def read_on_grid(path: Path, ref, resampling):
    with rasterio.open(path) as src:
        if src.crs == ref.crs and src.transform == ref.transform and src.shape == ref.shape:
            return src.read(1)
        dst = np.full(ref.shape, np.nan if src.dtypes[0].startswith("float") else 255,
                      dtype=src.dtypes[0])
        reproject(rasterio.band(src, 1), dst, dst_transform=ref.transform, dst_crs=ref.crs,
                  resampling=resampling)
        return dst


def folder_date(d: Path) -> str:
    return d.name.split("_")[2]


def process_pair(before_dir: Path, after_dir: Path, window: int) -> dict:
    track = before_dir.name.split("_")[0] + "_" + before_dir.name.split("_")[1]
    d1, d2 = folder_date(before_dir), folder_date(after_dir)
    with rasterio.open(find(before_dir, "HHHH")) as ref, rasterio.open(find(after_dir, "HHHH")) as aft:
        profile = ref.profile
        mb = read_on_grid(find(before_dir, "mask"), ref, Resampling.nearest)
        ma = read_on_grid(find(after_dir, "mask"), ref, Resampling.nearest)
        valid = (mb >= 1) & (mb <= 5) & (ma >= 1) & (ma <= 5)
        result = {"track_frame": track, "date_before": d1, "date_after": d2,
                  "before": before_dir.name, "after": after_dir.name,
                  "grid_crs": str(ref.crs), "pixel_m": ref.res[0], "after_native_pixel_m": aft.res[0],
                  "window_px": window,
                  "valid_pixels_both": int(valid.sum()), "total_pixels": int(valid.size)}
        for pol in ("HHHH", "HVHV"):
            b = read_on_grid(find(before_dir, pol), ref, Resampling.average)
            a = read_on_grid(find(after_dir, pol), ref, Resampling.average)
            ok = valid & np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0)
            bs, as_ = boxcar(b, ok, window), boxcar(a, ok, window)
            with np.errstate(invalid="ignore", divide="ignore"):
                db = 10.0 * np.log10(as_ / bs)
            db[~ok] = np.nan
            out = WORK / f"{track}_{d1}_{d2}_{pol}_logratio_dB.tif"
            prof = {**profile, "dtype": "float32", "nodata": np.nan, "compress": "deflate", "tiled": True}
            with rasterio.open(out, "w", **prof) as dst:
                dst.write(db.astype(np.float32), 1)
            v = db[np.isfinite(db)]
            result[pol] = {
                "file": out.relative_to(ROOT).as_posix(),
                "pct_px_drop_gt_3dB": round(float((v < -3).mean() * 100), 3),
                "pct_px_rise_gt_3dB": round(float((v > 3).mean() * 100), 3),
                "p01_p50_p99_dB": [round(float(x), 2) for x in np.percentile(v, [1, 50, 99])],
            }
    return result


def main():
    global RAW, WORK
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=5)
    ap.add_argument("--raw", default=str(RAW), help="folder of <track>_<frame>_<date>_<tag> dirs")
    ap.add_argument("--only", help="comma-separated track_frame keys, e.g. 098A_016")
    ap.add_argument("--gap-days", type=int, default=12, help="NISAR repeat interval; other gaps are skipped")
    ap.add_argument("--redo", action="store_true", help="recompute pairs that already have outputs")
    args = ap.parse_args()
    RAW = Path(args.raw).resolve()
    WORK = ROOT / "data" / "work" / "change" / RAW.name
    WORK.mkdir(parents=True, exist_ok=True)
    # Group the dated folders by track_frame; consecutive dates on one track form the pairs.
    tracks = {}
    for d in sorted(p for p in RAW.iterdir() if p.is_dir()):
        tracks.setdefault("_".join(d.name.split("_")[:2]), []).append(d)
    only = set(args.only.split(",")) if args.only else None
    sp = WORK / "summary.json"
    done = {}
    if sp.exists() and not args.redo:
        done = {(q["track_frame"], q["date_before"], q["date_after"]): q
                for q in json.loads(sp.read_text())["pairs"] if "date_before" in q}
    for key, dirs in sorted(tracks.items()):
        if only and key not in only:
            continue
        dirs = sorted(dirs, key=folder_date)
        for b, a in zip(dirs, dirs[1:]):
            k = (key, folder_date(b), folder_date(a))
            gap = (datetime.fromisoformat(k[2]) - datetime.fromisoformat(k[1])).days
            if gap != args.gap_days:      # only true repeat-pass steps (skips the Jul 27 - Aug 10 data gap)
                continue
            if k in done:
                continue
            try:
                print("processing", *k, flush=True)
                done[k] = process_pair(b, a, args.window)
            except FileNotFoundError as e:
                print("  skipped (download incomplete?):", e)
    summary = {"generated_utc": datetime.now(timezone.utc).isoformat(), "method": "boxcar log-ratio dB",
               "caveat": "Backscatter change is not proof of damage; see script docstring.",
               "pairs": [done[k] for k in sorted(done)]}
    sp.write_text(json.dumps(summary, indent=2))
    for q in summary["pairs"]:
        print(q["track_frame"], q["date_before"], "->", q["date_after"],
              "HH p01/p50/p99", q["HHHH"]["p01_p50_p99_dB"], "HV", q["HVHV"]["p01_p50_p99_dB"])


if __name__ == "__main__":
    main()
