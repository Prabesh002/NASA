"""
Terrain context from NASADEM (NASA, 1 arc-second, year 2000) and glacial lakes from NASA's HMA_GLI.

  1. Mosaic the NASADEM tiles and crop to the study box.
  2. Standard hydrological conditioning with pysheds (fill pits, fill depressions, resolve flats), then
     D8 flow direction (each cell points to its steepest downhill neighbour) and flow accumulation.
  3. Flow direction is written as an 8-bit PNG on the DEM's own lon/lat grid. The site follows these
     pointers from a clicked cell to draw the downhill route. 0 = none, 1..8 = N, NE, E, SE, S, SW, W, NW.
  4. Height above the nearest river channel (HAND): for every cell, its elevation minus the elevation of
     the river cell it drains to. "River" = cells with at least STREAM_KM2 of upstream area. Cells below
     HAND_CLASSES metres are written as a transparent overlay PNG on a Web Mercator grid.
  5. Glacial lakes of the 2015-2018 period inside the box are written as GeoJSON.

Limits (also shown on the site): NASADEM was measured in February 2000 and has metre-scale vertical
errors that grow on steep slopes, so narrow gorges are poorly resolved. HAND is a terrain screening, not
a flood model: no water volume, depth, speed, or defences. The downhill route is a geometric path.

Usage: python pipeline/terrain_context.py
SI disclosure: written with SI assistance (Claude, Anthropic). See docs/SI-USAGE.md.
"""
import datetime, json, math, pathlib, zipfile
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from PIL import Image
import shapefile
if not hasattr(np, "in1d"):
    np.in1d = np.isin                 # pysheds 0.5 still calls the name removed in numpy 2.4
from pysheds.grid import Grid

W, S, E, N = 85.05, 27.80, 85.70, 28.45
TILES = ["n27e085", "n28e085"]
STREAM_KM2 = 25.0
HAND_CLASSES = [10.0, 20.0]            # metres above the nearest river channel
CELL_3857 = 28.35                      # about 25 m on the ground at 28 N
RAW = pathlib.Path("data/raw/context")
WORK = pathlib.Path("data/work/terrain")
SITE = pathlib.Path("site/public/data")
R = 6378137.0
mx = lambda lon: math.radians(lon) * R
my = lambda lat: math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * R


def read_hgt(tile):
    with zipfile.ZipFile(RAW / "nasadem" / f"NASADEM_HGT_{tile}.zip") as z:
        name = next(n for n in z.namelist() if n.endswith(".hgt"))
        return np.frombuffer(z.read(name), ">i2").reshape(3601, 3601).astype("float32")


def main():
    WORK.mkdir(parents=True, exist_ok=True); SITE.mkdir(parents=True, exist_ok=True)
    south, north = read_hgt("n27e085"), read_hgt("n28e085")          # each: row 0 = north edge, 1 arc-second posting
    dem = np.vstack([north[:-1], south])                              # lat 29 .. 27, lon 85 .. 86 (cell centres on the posts)
    step = 1 / 3600
    c0, c1 = round((W - 85) / step), round((E - 85) / step)
    r0, r1 = round((29 - N) / step), round((29 - S) / step)
    dem = dem[r0:r1, c0:c1]
    h, w = dem.shape
    transform = from_origin(W - step / 2, N + step / 2, step, step)
    with rasterio.open(WORK / "dem.tif", "w", driver="GTiff", height=h, width=w, count=1, dtype="float32", crs="EPSG:4326",
                       transform=transform, nodata=-32768) as dst:
        dst.write(dem, 1)
    print("dem", dem.shape, float(dem.min()), float(dem.max()))

    grid = Grid.from_raster(str(WORK / "dem.tif"))
    d = grid.read_raster(str(WORK / "dem.tif"))
    cond = grid.resolve_flats(grid.fill_depressions(grid.fill_pits(d)))
    dirmap = (64, 128, 1, 2, 4, 8, 16, 32)                           # N, NE, E, SE, S, SW, W, NW
    fdir = grid.flowdir(cond, dirmap=dirmap)
    acc = grid.accumulation(fdir, dirmap=dirmap)
    cell_km2 = (step * 111.32) * (step * 111.32 * math.cos(math.radians((S + N) / 2)))
    streams = acc > STREAM_KM2 / cell_km2
    hand = np.asarray(grid.compute_hand(fdir, d, streams, dirmap=dirmap), "float32")
    fd = np.asarray(fdir)
    code = np.zeros(fd.shape, "uint8")
    for i, v in enumerate(dirmap):
        code[fd == v] = i + 1
    Image.fromarray(code, "L").save(SITE / "flowdir.png", optimize=True)
    np.save(WORK / "acc.npy", np.asarray(acc, "float32")); np.save(WORK / "hand.npy", hand)
    print("flowdir cells without direction:", int((code == 0).sum()), "| stream cells:", int(streams.sum()))

    # HAND classes on a Web Mercator grid so the overlay sits exactly on the map
    x0, x1, y0, y1 = mx(W), mx(E), my(S), my(N)
    ow, oh = round((x1 - x0) / CELL_3857), round((y1 - y0) / CELL_3857)
    hm = np.full((oh, ow), np.nan, "float32")
    reproject(hand, hm, src_transform=transform, src_crs="EPSG:4326", dst_transform=from_origin(x0, y1, CELL_3857, CELL_3857),
              dst_crs="EPSG:3857", resampling=Resampling.bilinear, src_nodata=np.nan, dst_nodata=np.nan)
    rgba = np.zeros((oh, ow, 4), "uint8")
    rgba[hm < HAND_CLASSES[1]] = (230, 159, 0, 150)                   # 10-20 m: orange
    rgba[hm < HAND_CLASSES[0]] = (120, 60, 160, 190)                  # under 10 m: purple
    Image.fromarray(rgba, "RGBA").save(SITE / "lowground.png", optimize=True)
    share = [float(np.nanmean(hm < c)) for c in HAND_CLASSES]

    # glacial lakes (NASA HMA_GLI, 2015-2018 period)
    rd = shapefile.Reader(str(RAW / "hma_gli" / "HMA_GLI_glacial_lakes_LatLonWGS84_2015_18"))
    feats = []
    for sr in rd.iterShapeRecords(bbox=[W, S, E, N]):
        rec = sr.record.as_dict()
        feats.append({"type": "Feature", "geometry": sr.shape.__geo_interface__,
                      "properties": {"area_m2": rec["Area_m2"], "elevation_m": round(rec["Z"]), "period": "2015 to 2018",
                                     "lon": rec["CENTROID_X"], "lat": rec["CENTROID_Y"], "id": rec["Geo_ID"]}})
    (SITE / "glacial_lakes.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))

    meta = {"generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "dem": "NASADEM_HGT v001 (NASA LP DAAC), tiles " + ", ".join(TILES) + ", 1 arc-second, acquired February 2000",
            "flowdir": {"file": "flowdir.png", "west": W - step / 2, "north": N + step / 2, "step_deg": step, "width": w, "height": h,
                        "codes": "0 none; 1..8 = N, NE, E, SE, S, SW, W, NW", "method": "pysheds: fill pits, fill depressions, resolve flats, D8"},
            "lowground": {"file": "lowground.png", "bounds_lonlat": [W, S, E, N], "classes_m": HAND_CLASSES, "stream_min_upstream_km2": STREAM_KM2,
                          "share_of_box": share, "method": "height above nearest drainage (HAND), pysheds compute_hand"},
            "lakes": {"file": "glacial_lakes.geojson", "count": len(feats), "source": "HMA_GLI v1 (NASA NSIDC DAAC), period 2015-2018"}}
    (SITE / "terrain.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta["lowground"]), len(feats), "lakes")


if __name__ == "__main__":
    main()
