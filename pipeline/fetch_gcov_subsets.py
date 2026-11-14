"""
Fetch NISAR GCOV backscatter subsets for the Rasuwa corridor, before and after the
Aug 2026 flood, via NASA Harmony. Harmony clips each ~7 GB HDF5 file to our box
and returns small Cloud-Optimized GeoTIFFs, so we never download the full files.

Provenance:
- Collection C2854338529-ASF = NISAR_L2_GCOV_PROVISIONAL_V1 (CMR, checked 2026-11-14).
- Granule IDs below come from a CMR granule search on 2026-11-14:
  bbox 85.10,27.85,85.50,28.40, temporal 2026-08-14 .. 2026-09-05.
  All use CRID P05023 (PROVISIONAL). Duplicate X05026 granules are excluded.
- Variable paths come from the collection's associated CMR UMM-Var records.

Usage (from the project root):
    python -m venv .venv && .venv\\Scripts\\activate
    pip install -r pipeline/requirements.txt
    python pipeline/fetch_gcov_subsets.py --dry-run   # print what would be requested
    python pipeline/fetch_gcov_subsets.py             # submit Harmony jobs, download

Requires EARTHDATA_TOKEN in .env. Never hard-code it.
Verified 2026-11-14: harmony-py's Client accepts token=.
Still UNVERIFIED until the first real run: Harmony job runtime and output file names.

SI disclosure: this script was written with SI assistance (Claude, Anthropic). See docs/SI-USAGE.md.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

COLLECTION_ID = "C2854338529-ASF"  # NISAR_L2_GCOV_PROVISIONAL_V1
# Named areas of interest. "corridor" = Rasuwagadhi/Timure -> Syabrubesi -> toward Betrawati.
# "source" = Lhende Khola valley + north face of Langtang Lirung, where ICIMOD/USGS place the
# rock-ice avalanche (Wikipedia infobox ~28.3N 85.5E; exact scar coords UNVERIFIED), down to the
# Rasuwagadhi confluence.
AOIS = {
    "corridor": dict(w=85.10, s=27.85, e=85.50, n=28.40),
    "source":   dict(w=85.33, s=28.20, e=85.65, n=28.42),
}
BBOX = AOIS["corridor"]
VARIABLES = [
    "/science/LSAR/GCOV/grids/frequencyA/HHHH",  # co-pol backscatter (real-valued)
    "/science/LSAR/GCOV/grids/frequencyA/HVHV",  # cross-pol backscatter (real-valued)
    "/science/LSAR/GCOV/grids/frequencyA/mask",  # validity / shadow-layover info
]

# Flood reported ~2026-08-26 (exact time UNVERIFIED). Before/after scene per track.
# The 'mode' field comes from the file name. Modes differ on tracks 048 and 149
# (4005 DHDH vs 2005 QPDH), so pixel spacing may differ (see research/nisar-notes.md).
# Track 098A uses the same mode before and after, so it's the cleanest comparison.
GRANULES = [
    # track 048 descending, frame 074
    dict(id="G4284786693-ASF", track="048D", frame="074", when="before", date="2026-08-16", mode="4005_DHDH"),
    dict(id="G4292184550-ASF", track="048D", frame="074", when="after",  date="2026-08-28", mode="2005_QPDH"),
    # track 048 descending, frame 075
    dict(id="G4284800841-ASF", track="048D", frame="075", when="before", date="2026-08-16", mode="4005_DHDH"),
    dict(id="G4292181877-ASF", track="048D", frame="075", when="after",  date="2026-08-28", mode="2005_QPDH"),
    # track 098 ascending, frame 016
    dict(id="G4286846660-ASF", track="098A", frame="016", when="before", date="2026-08-19", mode="4005_DHDH"),
    dict(id="G4296206881-ASF", track="098A", frame="016", when="after",  date="2026-08-31", mode="4005_DHDH"),
    # track 149 descending, frame 074
    dict(id="G4289473442-ASF", track="149D", frame="074", when="before", date="2026-08-23", mode="2005_QPDH"),
    dict(id="G4300190360-ASF", track="149D", frame="074", when="after",  date="2026-09-04", mode="4005_DHDH"),
    # Track 098A frame 016 time series for the "normal change" baseline. Same mode (4005 DHDH) and
    # same CRID (P05023, PROVISIONAL) as the event pair. IDs from a CMR granule search on 2026-11-14
    # (bbox 85.10,27.85,85.65,28.42; 2026-06-01 .. 2026-10-25). X05026 duplicates excluded.
    # Note: the Jul 14 file name carries "_F_F_" where the others have "_N_F_" (meaning not checked).
    dict(id="G4244912577-ASF", track="098A", frame="016", when="series", date="2026-06-20", mode="4005_DHDH"),
    dict(id="G4247502987-ASF", track="098A", frame="016", when="series", date="2026-07-02", mode="4005_DHDH"),
    dict(id="G4259618867-ASF", track="098A", frame="016", when="series", date="2026-07-14", mode="4005_DHDH"),
    dict(id="G4264276653-ASF", track="098A", frame="016", when="series", date="2026-07-26", mode="4005_DHDH"),
    dict(id="G4311502130-ASF", track="098A", frame="016", when="series", date="2026-09-12", mode="4005_DHDH"),
    dict(id="G4324047986-ASF", track="098A", frame="016", when="series", date="2026-09-24", mode="4005_DHDH"),
    dict(id="G4350937998-ASF", track="098A", frame="016", when="series", date="2026-10-06", mode="4005_DHDH"),
    dict(id="G4380217029-ASF", track="098A", frame="016", when="series", date="2026-10-18", mode="4005_DHDH"),
]

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "gcov"


def load_token() -> str:
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    tok = os.environ.get("EARTHDATA_TOKEN", "").strip()
    if not tok:
        sys.exit("EARTHDATA_TOKEN missing. Copy .env.example to .env and paste your Earthdata token there.")
    return tok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="comma-separated granule IDs to fetch (default: all)")
    ap.add_argument("--when", help="fetch only entries with this tag: before, after or series")
    ap.add_argument("--aoi", default="corridor", choices=sorted(AOIS))
    args = ap.parse_args()
    global BBOX, OUT
    BBOX = AOIS[args.aoi]
    if args.aoi != "corridor":
        OUT = OUT.parent / f"gcov_{args.aoi}"

    granules = GRANULES
    if args.only:
        keep = set(args.only.split(","))
        granules = [g for g in GRANULES if g["id"] in keep]
    if args.when:
        granules = [g for g in granules if g["when"] == args.when]

    if args.dry_run:
        print(f"Collection {COLLECTION_ID}, bbox {BBOX}")
        print("Variables:", *VARIABLES, sep="\n  ")
        for g in granules:
            print(f"  {g['id']}  {g['track']}/{g['frame']}  {g['when']:6} {g['date']}  {g['mode']}")
        return

    from harmony import BBox, Client, Collection, Request

    client = Client(token=load_token())
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []

    for g in granules:
        dest = OUT / f"{g['track']}_{g['frame']}_{g['date']}_{g['when']}"
        dest.mkdir(parents=True, exist_ok=True)
        req = Request(
            collection=Collection(id=COLLECTION_ID),
            granule_id=[g["id"]],
            spatial=BBox(**BBOX),
            variables=VARIABLES,
            format="image/tiff",
        )
        print(f"Submitting {g['id']} ({g['track']} {g['when']} {g['date']}) ...", flush=True)
        job_id = client.submit(req)
        client.wait_for_processing(job_id, show_progress=True)
        files = [f.result() for f in client.download_all(job_id, directory=str(dest), overwrite=True)]
        manifest.append({
            **g,
            "collection": COLLECTION_ID,
            "harmony_job_id": job_id,
            "bbox": BBOX,
            "variables": VARIABLES,
            "files": [str(Path(f).relative_to(ROOT)) for f in files],
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        })
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f"  -> {len(files)} file(s) in {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
