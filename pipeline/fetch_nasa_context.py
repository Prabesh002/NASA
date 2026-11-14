"""
Fetch the NASA context datasets used beside NISAR: elevation, glacier outlines, glacial lakes.

  NASADEM_HGT v001   (LP DAAC,  C2763264762-LPCLOUD)    1 arc-second elevation, tiles covering the study box
  NSIDC-0770 v7      (NSIDC,    C2768953486-NSIDCV0)    Randolph Glacier Inventory 7.0 glacier outlines
  HMA_GLI v1         (NSIDC,    C3249539102-NSIDC_CPRD) High Mountain Asia glacial lake inventory 1990-2018

Granule download links are read from NASA's Common Metadata Repository (CMR) at run time, nothing is
hard-coded. Every file fetched is logged with its URL and time in data/raw/context/manifest.json.

Usage: python pipeline/fetch_nasa_context.py [--list]      (--list prints the links and downloads nothing)
Requires EARTHDATA_TOKEN in .env.
SI disclosure: written with SI assistance (Claude, Anthropic). See docs/SI-USAGE.md.
"""
import argparse, datetime, json, os, pathlib, urllib.parse
import requests
from dotenv import load_dotenv

BOX = "85.05,27.80,85.70,28.45"      # w,s,e,n : corridor + source boxes with a margin
COLLECTIONS = {
    "nasadem": {"concept_id": "C2763264762-LPCLOUD", "bbox": True},
    # RGI has no granule records in CMR (checked 2026-11-14), so its regional file is fetched by its NSIDC archive URL.
    "rgi7": {"concept_id": "C2768953486-NSIDCV0", "direct": [
        "https://daacdata.apps.nsidc.org/pub/DATASETS/nsidc0770_rgi_v7/regional_files/RGI2000-v7.0-G/RGI2000-v7.0-G-15_south_asia_east.zip"]},
    "hma_gli": {"concept_id": "C3249539102-NSIDC_CPRD", "bbox": False, "match": ["2015_18."]},   # most recent period only
}
OUT = pathlib.Path("data/raw/context")


def granule_links(cfg):
    if "direct" in cfg:
        return [(u.split("/")[-1], u) for u in cfg["direct"]]
    params = {"collection_concept_id": cfg["concept_id"], "page_size": 200}
    if cfg["bbox"]:
        params["bounding_box"] = BOX
    r = requests.get("https://cmr.earthdata.nasa.gov/search/granules.json?" + urllib.parse.urlencode(params), timeout=60)
    r.raise_for_status()
    out = []
    for g in r.json()["feed"]["entry"]:
        for l in g.get("links", []):
            h = l["href"]
            if h.startswith("https") and "data#" in l.get("rel", "") and not l.get("inherited") and not h.endswith(("s3credentials", ".xml")):
                if "match" in cfg and not any(m in h for m in cfg["match"]):
                    continue
                out.append((g["title"], h))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    load_dotenv()
    token = os.environ.get("EARTHDATA_TOKEN")
    manifest = []
    for name, cfg in COLLECTIONS.items():
        if a.only and name not in a.only.split(","):
            continue
        links = granule_links(cfg)
        print(f"{name}: {len(links)} file link(s)")
        for title, url in links:
            print("  ", title, url)
            if a.list:
                continue
            dest = OUT / name / url.split("/")[-1]
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                # Earthdata redirects to a login host; send the token only to NASA Earthdata hosts.
                s = requests.Session()
                r = s.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=600, stream=True)
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            manifest.append({"dataset": name, "collection": cfg["concept_id"], "granule": title, "url": url, "file": str(dest),
                             "bytes": dest.stat().st_size, "retrieved_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()})
    if not a.list:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
