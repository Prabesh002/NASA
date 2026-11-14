"""
How strong is the radar change along the river, and is it more than ordinary 12-day change?

Steps
  1. Build drainage paths from OpenStreetMap waterways (data/raw/osm/osm_context.json). OSM draws
     waterways in the direction of flow, so we follow them downstream from a start point.
       - "flood": from the head of the change signal north of Langtang Lirung (start point picked
         from the NISAR change map, see START below) down the Lende Khola, Bhote Koshi and Trishuli
         to Betrawati.
       - controls: rivers that join the same system but, per the published accounts, did not carry
         the debris flow (upper Lende Khola above the tributary junction, Kyirong Tsangpo above the
         Rasuwagadhi confluence, Langtang Khola, Chilime Khola).
  2. For every 12-day step on track 098A (HH and HV), take the pixels within BUFFER_M of the path and
     group them into BIN_M-long bins by distance downstream. Per bin: mean absolute change (dB) and
     the share of pixels whose change exceeds +-3 dB.
  3. Write site/public/data/river_stats.json and flowpath.geojson.

The step Aug 19 -> Aug 31 contains the flood. All other steps are the "ordinary change" baseline.
Caveat: OSM centre lines can sit tens of metres off the true channel, the valley floor is in places
narrower than the buffer, and steep slopes distort radar geometry. The numbers are a description of
the measurements, not a damage estimate.

Usage: python pipeline/river_stats.py
SI disclosure: written with SI assistance (Claude, Anthropic). See docs/SI-USAGE.md.
"""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import transform as warp_transform

ROOT = Path(__file__).resolve().parent.parent
OSM = ROOT / "data/raw/osm/osm_context.json"
CH = ROOT / "data/work/change"
OUT = ROOT / "site/public/data"
BUFFER_M, BIN_M, STEP_M = 100.0, 500.0, 10.0
TRACK = "098A_016"
EVENT = ("2026-08-19", "2026-08-31")

# (lon, lat) start points and stop points. "flood" start = upper end of the continuous change track
# seen in the 098A Aug 19 -> Aug 31 change map (read off the map by eye, +-200 m).
PATHS = {
    "flood":   dict(label="Flood path: Langtang Lirung north side to Betrawati",
                    start=(85.525, 28.289), stop=(85.1860, 27.9731)),
    "lende_upper": dict(label="Control: upper Lende Khola (above the tributary junction)",
                        start=(85.4421, 28.4383), stop=(85.4307, 28.3304), max_km=12),
    "kyirong": dict(label="Control: Kyirong Tsangpo (above the Rasuwagadhi confluence)",
                    start=(85.3575, 28.3681), stop=(85.3770, 28.2781), max_km=14),
    "langtang": dict(label="Control: Langtang Khola", start=(85.47, 28.205), stop=(85.3413, 28.1644), max_km=16),
    "chilime": dict(label="Control: Chilime Khola", start=(85.25, 28.21), stop=(85.3428, 28.1812), max_km=12),
}
PLACES = {  # OSM place nodes (retrieved with the waterways); used for km marks only
    "Rasuwagadhi": (85.3777789, 28.2777749), "Syabrubesi": (85.3427433, 28.164569),
    "Betrawati": (85.1859528, 27.9731085),
}


def to_utm(lons, lats):
    x, y = warp_transform("EPSG:4326", "EPSG:32645", list(lons), list(lats))
    return np.array(x), np.array(y)


def load_ways():
    els = json.loads(OSM.read_text(encoding="utf-8"))["elements"]
    ways = [e for e in els if e["type"] == "way" and e.get("tags", {}).get("waterway") in ("river", "stream")]
    for w in ways:
        w["pts"] = [(round(g["lon"], 7), round(g["lat"], 7)) for g in w["geometry"]]
    return ways


def trace(ways, start, stop, max_km=None):
    """Follow waterways downstream from the vertex nearest to start, until nearest to stop."""
    index = {}
    for wi, w in enumerate(ways):
        for pi, p in enumerate(w["pts"][:-1]):       # a way can be entered at any vertex but its last
            index.setdefault(p, []).append((wi, pi))
    allpts = np.array([p for w in ways for p in w["pts"]])
    owner = [(wi, pi) for wi, w in enumerate(ways) for pi in range(len(w["pts"]))]
    k = np.cos(np.radians(28.2))
    d = np.hypot((allpts[:, 0] - start[0]) * k, allpts[:, 1] - start[1])
    wi, pi = owner[int(d.argmin())]
    start_off_m = float(d.min()) * 111320
    path, names, seen = [], [], set()
    while True:
        if wi in seen:
            break
        seen.add(wi)
        w = ways[wi]
        nm = w["tags"].get("name:en") or w["tags"].get("name") or "(unnamed)"
        if not names or names[-1] != nm:
            names.append(nm)
        path.extend(w["pts"][pi:])
        nxt = [c for c in index.get(w["pts"][-1], []) if c[0] not in seen]
        if not nxt:
            break
        # prefer rivers over streams when several ways leave the node
        nxt.sort(key=lambda c: ways[c[0]]["tags"]["waterway"] != "river")
        wi, pi = nxt[0]
    p = np.array(path)
    dstop = np.hypot((p[:, 0] - stop[0]) * k, p[:, 1] - stop[1])
    end = int(dstop.argmin())
    p = p[: end + 1]
    x, y = to_utm(p[:, 0], p[:, 1])
    seg = np.hypot(np.diff(x), np.diff(y))
    keep = np.r_[True, seg > 0]
    p, x, y = p[keep], x[keep], y[keep]
    km = np.r_[0, np.cumsum(np.hypot(np.diff(x), np.diff(y)))] / 1000
    if max_km:
        m = km <= max_km
        p, x, y, km = p[m], x[m], y[m], km[m]
    return dict(lonlat=p, x=x, y=y, km=km, names=names, start_off_m=start_off_m,
                stop_off_m=float(dstop.min()) * 111320)


def densify(path):
    total = path["km"][-1] * 1000
    s = np.arange(0, total, STEP_M)
    return np.interp(s, path["km"] * 1000, path["x"]), np.interp(s, path["km"] * 1000, path["y"]), s


def bin_raster(shape, tf, xs, ys, s):
    """Raster of bin ids (-1 = outside buffer). Each pixel takes the bin of the nearest path station."""
    best = np.full(shape, np.inf, np.float32)
    ids = np.full(shape, -1, np.int16)
    r = int(math.ceil(BUFFER_M / tf.a)) + 1
    cols = (xs - tf.c) / tf.a
    rows = (ys - tf.f) / tf.e
    for c, rr, x, y, sm in zip(cols, rows, xs, ys, s):
        c0, r0 = int(c), int(rr)
        a, b = max(r0 - r, 0), min(r0 + r + 1, shape[0])
        cc, dd = max(c0 - r, 0), min(c0 + r + 1, shape[1])
        if a >= b or cc >= dd:
            continue
        px = tf.c + (np.arange(cc, dd) + 0.5) * tf.a
        py = tf.f + (np.arange(a, b) + 0.5) * tf.e
        dist = np.hypot(px[None, :] - x, py[:, None] - y).astype(np.float32)
        win = best[a:b, cc:dd]
        m = (dist <= BUFFER_M) & (dist < win)
        win[m] = dist[m]
        ids[a:b, cc:dd][m] = int(sm // BIN_M)
    return ids


def main():
    ways = load_ways()
    pairs = sorted({tuple(p.name.split("_")[2:4]) for p in (CH / "gcov").glob(f"{TRACK}_*_HHHH_logratio_dB.tif")})
    out = dict(generated_utc=datetime.now(timezone.utc).isoformat(), track=TRACK, buffer_m=BUFFER_M, bin_m=BIN_M,
               event_pair=list(EVENT), pairs=[list(p) for p in pairs],
               method="mean |dB change| and share of pixels beyond +-3 dB, within buffer_m of the OSM "
                      "waterway centre line, per bin_m of distance downstream; 5x5 boxcar log-ratio",
               source="NISAR L2 GCOV PROVISIONAL (CRID P05023) via NASA Harmony; OSM waterways (ODbL)",
               paths={})
    features = []
    for key, cfg in PATHS.items():
        path = trace(ways, cfg["start"], cfg["stop"], cfg.get("max_km"))
        xs, ys, s = densify(path)
        nb = int(s[-1] // BIN_M) + 1
        print(f"{key}: {path['km'][-1]:.1f} km, start snapped {path['start_off_m']:.0f} m, "
              f"stop {path['stop_off_m']:.0f} m, via {' > '.join(path['names'])}")
        rec = dict(label=cfg["label"], length_km=round(float(path["km"][-1]), 2), osm_names=path["names"],
                   bin_km=[round((i + 0.5) * BIN_M / 1000, 2) for i in range(nb)], series={})
        if key == "flood":
            px, py = to_utm([v[0] for v in PLACES.values()], [v[1] for v in PLACES.values()])
            rec["places_km"] = {}
            for name, ax, ay in zip(PLACES, px, py):
                dd = np.hypot(path["x"] - ax, path["y"] - ay)
                rec["places_km"][name] = dict(km=round(float(path["km"][dd.argmin()]), 1),
                                              off_path_m=round(float(dd.min())))
            print("  places:", rec["places_km"])
        cache = {}
        for d1, d2 in pairs:
            for pol in ("HHHH", "HVHV"):
                sums = np.zeros(nb); cnt = np.zeros(nb); big = np.zeros(nb); sgn = np.zeros(nb)
                for area in ("gcov", "gcov_source"):
                    f = CH / area / f"{TRACK}_{d1}_{d2}_{pol}_logratio_dB.tif"
                    if not f.exists():
                        continue
                    with rasterio.open(f) as r:
                        ck = (area, r.shape, tuple(r.transform)[:6])
                        if ck not in cache:
                            ids = bin_raster(r.shape, r.transform, xs, ys, s)
                            if area == "gcov_source":   # use the source box only beyond the corridor box
                                with rasterio.open(CH / "gcov" / f.name) as c:
                                    b = c.bounds
                                cx = r.transform.c + (np.arange(r.width) + 0.5) * r.transform.a
                                cy = r.transform.f + (np.arange(r.height) + 0.5) * r.transform.e
                                inside = ((cx[None, :] > b.left) & (cx[None, :] < b.right)
                                          & (cy[:, None] > b.bottom) & (cy[:, None] < b.top))
                                ids[inside] = -1
                            cache[ck] = ids
                        ids = cache[ck]
                        v = r.read(1)
                    m = (ids >= 0) & np.isfinite(v)
                    i, vv = ids[m], v[m]
                    sums += np.bincount(i, np.abs(vv), nb); cnt += np.bincount(i, None, nb)
                    big += np.bincount(i, np.abs(vv) > 3, nb); sgn += np.bincount(i, vv, nb)
                with np.errstate(invalid="ignore", divide="ignore"):
                    rec["series"].setdefault(f"{d1}_{d2}", {})[pol] = dict(
                        mean_abs_dB=[None if c < 20 else round(a / c, 3) for a, c in zip(sums, cnt)],
                        pct_beyond_3dB=[None if c < 20 else round(100 * a / c, 2) for a, c in zip(big, cnt)],
                        mean_dB=[None if c < 20 else round(a / c, 3) for a, c in zip(sgn, cnt)],
                        n_px=[int(c) for c in cnt],
                        whole_path=dict(mean_abs_dB=round(float(sums.sum() / max(cnt.sum(), 1)), 3),
                                        pct_beyond_3dB=round(float(100 * big.sum() / max(cnt.sum(), 1)), 2),
                                        n_px=int(cnt.sum())))
        out["paths"][key] = rec
        step = max(1, len(path["lonlat"]) // 2000)
        coords = [[float(a), float(b)] for a, b in path["lonlat"][::step]]
        features.append(dict(type="Feature", properties=dict(id=key, label=cfg["label"],
                             length_km=rec["length_km"]),
                             geometry=dict(type="LineString", coordinates=coords)))
        if key == "flood":
            for kmark in range(0, int(path["km"][-1]) + 1, 5):
                j = int(np.abs(path["km"] - kmark).argmin())
                features.append(dict(type="Feature", properties=dict(id="km", km=kmark),
                                     geometry=dict(type="Point", coordinates=[float(path["lonlat"][j][0]),
                                                                              float(path["lonlat"][j][1])])))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "river_stats.json").write_text(json.dumps(out))
    (OUT / "flowpath.geojson").write_text(json.dumps(dict(
        type="FeatureCollection", features=features,
        attribution="Waterway lines (c) OpenStreetMap contributors, ODbL 1.0")))
    print("\nwhole-path summary (HH): mean |dB|, % px beyond 3 dB")
    for key, rec in out["paths"].items():
        for pr, v in rec["series"].items():
            w = v["HHHH"]["whole_path"]
            flag = "  <-- flood step" if pr == "_".join(EVENT) else ""
            print(f"  {key:12s} {pr}  {w['mean_abs_dB']:.2f} dB  {w['pct_beyond_3dB']:5.1f} %  n={w['n_px']}{flag}")


if __name__ == "__main__":
    main()
