# Rasuwa flood, 26 August 2026: traced with NISAR radar

NASA Space Apps Challenge 2026, challenge "Dancing with the SARs". Local event: Ithari, Nepal.

An interactive story map that follows the Rasuwa flood from its source north of Langtang Lirung down the
Lende Khola, Bhote Koshi and Trishuli to Betrawati, using change detection on NASA-ISRO NISAR radar data.

Main result: across the flood (19 to 31 August), 20.7% of the radar pixels within 100 m of the river
changed by more than 3 dB. In seven other 12-day periods from June to October the figure was 0.8% to 3.8%,
and four neighbouring rivers showed no jump on the same dates.

Live site: https://nasa.nesomotions.com (after deployment). Slides: `/slide/` (seven slides, for the submission) and
`/local-presentation/` (full 11-slide talk for the in-room presentation).

## What you can do on the site

| Tab | What it shows |
|---|---|
| Flood | Where the ground changed across the flood. A slider compares it with a normal 12 days, and the flood can be played down the valley with the reported times. |
| Over time | All eight 12-day periods from June to October in date order, so the flood period can be compared with the others. |
| Glaciers | Radar echo of glacier ice on each date compared with 20 June, with glacial lakes from a NASA inventory. A weaker echo may be a sign of melt; we did not verify it. |
| Water paths | Click a point and a line follows the slope downhill (NASADEM). Also shades low ground beside rivers. It does not forecast floods. |

Clicking the map in the Flood or Over time tab opens the radar record of that spot on ten dates, with a CSV download.
The story column has Back and Next buttons (and arrow keys) for presenting.

This is a hackathon prototype. It is not an official assessment, forecast or warning.

## What is in this repository

| Path | What |
|---|---|
| `site/public/` | The website (static HTML, CSS, JavaScript, map tiles, statistics). Served by Cloudflare Workers static assets. |
| `pipeline/` | Reproducible data scripts (Python and Node.js). |
| `research/` | Official challenge texts, rules, event facts with sources, data provenance (`data-sources.md`). |
| `docs/SI-USAGE.md` | Log of where and how SI was used. |
| `wrangler.jsonc` | Cloudflare deploy configuration. |

`data/` (raw NISAR subsets and intermediate rasters, several GB) is not committed. The pipeline re-creates it.

## Reproduce the data

Needs Python 3.11+, Node.js 20+, and a free NASA Earthdata Login token in `.env` as `EARTHDATA_TOKEN=...`.

```
python -m venv .venv
.venv\Scripts\activate                              # Windows; use source .venv/bin/activate elsewhere
pip install -r pipeline/requirements.txt

python pipeline/fetch_gcov_subsets.py               # NISAR GCOV subsets, corridor box, via NASA Harmony
python pipeline/fetch_gcov_subsets.py --aoi source  # same scenes, source-zone box
node pipeline/fetch_osm.mjs                         # rivers, places, peaks from OpenStreetMap

python pipeline/change_detection.py                 # 12-day log-ratio change, corridor
python pipeline/change_detection.py --raw data/raw/gcov_source
python pipeline/river_stats.py                      # change along river paths, baseline and controls
python pipeline/make_tiles.py                       # web map tiles and layer index

python pipeline/make_series.py                      # ten-date radar record used by the click card
python pipeline/fetch_nasa_context.py               # NASADEM elevation and the HMA glacial lake inventory
python pipeline/terrain_context.py                  # flow directions and low ground beside rivers
python pipeline/glacier_season.py                   # glacier echo on each date against 20 June
python pipeline/build_research_page.py              # site/public/research.html from docs/DATA-METHODS.md
```

How each step works is written up in `docs/DATA-METHODS.md` (also on the site as "Data and methods").

## Run and deploy the site

```
python -m http.server 8788 --directory site/public   # local preview at http://localhost:8788
npx wrangler dev        # or the Cloudflare preview at http://localhost:8787
npx wrangler deploy     # Cloudflare Workers static assets, custom domain nasa.nesomotions.com
```

## Method in short

1. NASA Harmony clips NISAR L2 GCOV layers (HHHH, HVHV, mask) to the study area as GeoTIFFs.
2. For consecutive passes on the same track (12 days apart): drop masked pixels, average power in a
   5 x 5 window, change = 10 log10(after / before) in dB.
3. River paths are traced downstream along OpenStreetMap waterways. Within 100 m of a path, per 500 m of
   distance downstream, we report the share of pixels that changed by more than 3 dB.
4. The same statistic for every other 12-day step from June to October 2026, and for four neighbouring
   rivers, gives a baseline of ordinary change.

Limits are listed on the site ("How we know") and in `site/public/credits.html`.

## Data and credits

- NISAR L2 GCOV, provisional release (CRID P05023): NASA/JPL and ISRO, distributed by the Alaska Satellite
  Facility DAAC, accessed through NASA Harmony.
- NASADEM_HGT version 1 (NASA LP DAAC) for elevation. High Mountain Asia glacial lake inventory version 1
  (NASA NSIDC DAAC) for the lakes.
- OpenStreetMap contributors (ODbL 1.0). OpenFreeMap / OpenMapTiles basemap. Mapzen Terrain Tiles (AWS Open Data).
- MapLibre GL JS 4.7.1 (BSD-3-Clause). Fonts: Archivo, Source Serif 4 (SIL OFL).
- Event references: ICIMOD, The Kathmandu Post. Full list with dates: `research/data-sources.md`.

## SI disclosure

The idea, study area and audience are the team's own. The code in `pipeline/` and `site/`, the slides and
the wording of the site text were written with SI assistance (Claude, Anthropic), from sources the team chose
and checked. No SI-generated images,
video or audio are used. Full log: `docs/SI-USAGE.md`.

No NASA logos or insignia are used. NASA does not endorse this project.
