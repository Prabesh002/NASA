"""
How the radar echo of the glaciers changed through the 2026 season (NISAR track 098A, HH).

Uses the 50 m dB stack from make_series.py. Inside glacier outlines only:
  1. For every date after the first, dB(date) - dB(first date, 20 June), written as a transparent overlay
     PNG (blue = echo fell, red = echo rose; transparent below 1.5 dB, full colour from 4 dB).
  2. Median dB per elevation band (NASADEM) per date, written to glacier_season.json for the chart.

Why it is of interest: liquid water in snow absorbs radar, so a falling echo over a snow-covered glacier
is a commonly used sign of surface melt (NASA's HMA_GSM dataset maps glacier melt and freeze timing from
SAR on that basis). UNVERIFIED here: we have no ground or weather data to confirm melt on these dates,
NISAR is L-band (less sensitive to wet snow than C-band), and new snowfall, exposed ice and debris also
change the echo. The site states this.

Glacier outlines: OpenStreetMap natural=glacier polygons (the RGI 7.0 download from NSIDC needs an
interactive Earthdata login that the script could not complete on 2026-11-14).

Usage: python pipeline/glacier_season.py      (run make_series.py and terrain_context.py first)
SI disclosure: written with SI assistance (Claude, Anthropic). See docs/SI-USAGE.md.
"""
import datetime, json, math, pathlib
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling, transform_geom
from PIL import Image

BANDS = [(4500, 5000), (5000, 5500), (5500, 6000), (6000, 7500)]
T0, T1 = 1.5, 4.0
SITE = pathlib.Path("site/public/data/glacier")
R = 6378137.0


def main():
    g = json.load(open("data/work/series/grid.json"))
    T = from_origin(g["x0"], g["y1"], g["cell"], g["cell"]); shape = (g["height"], g["width"]); dates = g["dates"]
    stack = np.load("data/work/series/hh_stack.npy")
    osm = json.load(open("data/raw/osm/osm_context.json", encoding="utf-8"))
    polys, feats = [], []
    for e in osm["elements"]:
        if e.get("tags", {}).get("natural") == "glacier" and e["type"] == "way" and len(e.get("geometry", [])) > 3:
            ring = [[round(p["lon"], 5), round(p["lat"], 5)] for p in e["geometry"]]
            if ring[0] != ring[-1]:
                ring.append(ring[0])
            geom = {"type": "Polygon", "coordinates": [ring]}
            polys.append(transform_geom("EPSG:4326", "EPSG:3857", geom))
            feats.append({"type": "Feature", "geometry": geom, "properties": {"name": e["tags"].get("name:en") or e["tags"].get("name") or ""}})
    glacier = rasterize(polys, out_shape=shape, transform=T).astype(bool)
    with rasterio.open("data/work/terrain/dem.tif") as d:
        dem = np.full(shape, np.nan, "float32")
        reproject(d.read(1), dem, src_transform=d.transform, src_crs=d.crs, dst_transform=T, dst_crs="EPSG:3857", resampling=Resampling.bilinear)
    valid = glacier & np.isfinite(stack).all(0)

    SITE.mkdir(parents=True, exist_ok=True)
    files = []
    for i, date in enumerate(dates[1:], 1):
        diff = np.where(valid, stack[i] - stack[0], np.nan)
        a = np.clip((np.abs(diff) - T0) / (T1 - T0), 0, 1)
        rgba = np.zeros(shape + (4,), "uint8")
        rgba[diff < 0, :3] = (33, 102, 172); rgba[diff > 0, :3] = (178, 24, 43)
        rgba[..., 3] = np.where(np.isfinite(diff), a * 235, 0).astype("uint8")
        name = f"diff-{date.replace('-', '')}.png"
        Image.fromarray(rgba, "RGBA").save(SITE / name, optimize=True); files.append(name)
    bands = []
    for lo, hi in BANDS:
        m = valid & (dem >= lo) & (dem < hi)
        bands.append({"from_m": lo, "to_m": hi, "pixels": int(m.sum()), "area_km2": round(float(m.sum()) * 0.0025, 1),
                      "median_db": [round(float(np.median(stack[i][m])), 2) for i in range(len(dates))],
                      "share_fell_3db_vs_first": [round(float(np.mean((stack[i][m] - stack[0][m]) < -3)) * 100, 1) for i in range(len(dates))]})
        print(lo, hi, bands[-1]["pixels"], bands[-1]["median_db"], bands[-1]["share_fell_3db_vs_first"])
    lon = lambda x: math.degrees(x / R); lat = lambda y: math.degrees(2 * math.atan(math.exp(y / R)) - math.pi / 2)
    x1, y0 = g["x0"] + g["cell"] * g["width"], g["y1"] - g["cell"] * g["height"]
    meta = {"generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "dates": dates, "reference_date": dates[0],
            "overlay_files": files, "overlay_dates": dates[1:],
            "corners_lonlat": [[lon(g["x0"]), lat(g["y1"])], [lon(x1), lat(g["y1"])], [lon(x1), lat(y0)], [lon(g["x0"]), lat(y0)]],
            "glacier_area_measured_km2": round(float(valid.sum()) * 0.0025, 1), "bands": bands,
            "outline_source": "OpenStreetMap natural=glacier (ODbL), retrieved 2026-11-14", "elevation_source": "NASADEM_HGT v001",
            "radar_source": "NISAR L2 GCOV PROVISIONAL (CRID P05023), track 098A frame 016, HH, about 50 m cells",
            "interpretation": "UNVERIFIED: a falling echo over snow is a commonly used sign of surface melt; not confirmed here with ground or weather data."}
    (SITE / "glacier_season.json").write_text(json.dumps(meta, indent=1))
    (SITE / "glaciers.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))


if __name__ == "__main__":
    main()
