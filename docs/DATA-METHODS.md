# How the data was found, extracted and used

Written 2026-11-14 with SI assistance (Claude, Anthropic). Every step below is a script in `pipeline/` that you can re-run. Full provenance table: `research/data-sources.md`.

## The short version

1. I took NISAR radar images of the Rasuwa valley from NASA, for 10 dates between June and October 2026.
2. For every pair of dates 12 days apart, I divided the later image by the earlier one. Where the answer is far from 1, the ground changed.
3. I counted how much ground near the river changed in the 12 days that contain the flood (19 to 31 August), and compared it with the seven other 12-day periods and with four nearby rivers the flood did not go down.
4. Result: 20.7% of the riverside ground changed in the flood period. In ordinary periods it was 0.8% to 3.8%. The four other rivers stayed in their ordinary range.

## 1. Which NASA data

| | |
|---|---|
| Mission | NISAR, the NASA and ISRO L-band radar satellite |
| Product | Level 2 GCOV (geocoded polarimetric covariance), which is radar backscatter already placed on a map grid |
| NASA collection | `NISAR_L2_GCOV_PROVISIONAL_V1`, CMR id `C2854338529-ASF`, processing version P05023 |
| Archive | Alaska Satellite Facility DAAC (a NASA data centre) |
| Layers used | HHHH and HVHV backscatter (gamma-0 power) and the validity mask, frequency A |
| Maturity | "Provisional": calibrated, not yet fully validated. We say this on the site. |

Scenes used:

| Track | Dates (2026) | Why |
|---|---|---|
| 98 ascending, frame 16 | 20 Jun, 2 Jul, 14 Jul, 26 Jul, 19 Aug, 31 Aug, 12 Sep, 24 Sep, 6 Oct, 18 Oct | Main series. Same radar mode on every date, so the dates are comparable. All numbers come from this track. |
| 48 descending, frames 74 and 75 | 16 Aug, 28 Aug | Second look at the flood from another direction |
| 149 descending, frame 74 | 23 Aug, 4 Sep | Third look |

There is a gap in the series between 26 July and 19 August, so that step is not used.

## 2. How it was found and downloaded

- **Finding the scenes.** A search of NASA's Common Metadata Repository (CMR) for the collection above, inside the box 85.10 to 85.50°E, 27.85 to 28.40°N. The scene ids are listed in `pipeline/fetch_gcov_subsets.py`.
- **Downloading only what is needed.** One full NISAR file is about 7 GB. Instead of downloading whole files, the script asks NASA Harmony (NASA's subsetting service) to cut out two boxes and return small GeoTIFFs:
  - river corridor: 85.10 to 85.50°E, 27.85 to 28.40°N
  - source zone: 85.33 to 85.65°E, 28.20 to 28.42°N
- **Output.** GeoTIFFs in UTM zone 45N (EPSG:32645) in `data/raw/gcov/` and `data/raw/gcov_source/`. Each Harmony job id is logged in `manifest.json` in those folders.
- **Login.** A free NASA Earthdata account token, kept in `.env` and never committed.

Script: `pipeline/fetch_gcov_subsets.py`

## 3. Change detection

For each pair of consecutive dates on the same track:

1. Read the "before" and "after" backscatter and the mask.
2. Put the after image on the before image's pixel grid.
3. Average over 5 × 5 pixels. Radar images are grainy (speckle); this calms the grain.
4. Change in decibels = 10 × log10(after ÷ before), only where both dates are valid.
5. Save the result as a GeoTIFF in `data/work/change/`.

0 dB means no change. +3 dB means the echo doubled, −3 dB means it halved.

Script: `pipeline/change_detection.py`

## 4. Is the flood change more than normal?

1. Trace the river downstream using OpenStreetMap river lines, from the head of the change signal north of Langtang Lirung to Betrawati: 66.3 km.
2. Take every pixel within 100 m of that line and group the pixels into 500 m steps along the river.
3. For each step and each 12-day period, compute the share of pixels that changed by more than 3 dB.
4. Do the same for four control rivers that join the same system but are not in the flood's reported path: upper Lende Khola, Kyirong Tsangpo, Langtang Khola, Chilime Khola.

| | Share of riverside pixels changed by more than 3 dB (HH) |
|---|---|
| Flood path, 19 to 31 Aug | **20.69%** of 129,965 pixels |
| Flood path, seven ordinary periods | 0.76% to 3.83% |
| Control rivers, 19 to 31 Aug | 0.19%, 3.84%, 0.25%, 0.73% (each inside its own ordinary range) |

Script: `pipeline/river_stats.py`. Output: `site/public/data/river_stats.json`.

## 5. From rasters to the website

- `pipeline/make_tiles.py` reprojects the change rasters to web map tiles and colours them: red where the echo rose, blue where it fell, transparent below 1.5 dB.
- The site is static files on Cloudflare. The browser only draws; it does not compute or estimate any number.

## 5a. The record for any spot you click

- `pipeline/make_series.py` puts the HH backscatter of all ten track 98 dates on one grid of about 50 m and saves one small greyscale image per date. Averaging 10 m pixels to 50 m also reduces the radar grain.
- When you click the map, the browser reads the pixel under the click from each of the ten images and plots the ten values. The CSV button saves exactly those values.
- Pixel value to decibels: dB = −35 + (pixel − 1) × 0.15. Pixel 0 means no valid data.

## 5b. The Over time view

The same change calculation as in section 3, for all eight 12-day pairs on track 98. The Over time tab shows them in date order. Share of riverside ground changed by more than 3 dB, per period: 1.42%, 1.25%, 1.01% (June and July), **20.69%** (19 to 31 August), 3.67%, 1.07%, 3.83%, 0.76% (September and October). There is no pair between 26 July and 19 August in the data we used.

## 5c. Glaciers

- `pipeline/glacier_season.py` takes the 50 m series, keeps only pixels inside glacier outlines, and for each date subtracts the 20 June value. Blue = echo fell, red = echo rose.
- It also groups glacier pixels by height (NASADEM) and reports the median echo per date.
- Measured: above 6,000 m, the share of glacier pixels more than 3 dB below their 20 June value rose to 32.9% on 31 August and was back to 7.2% on 18 October.
- **Unverified interpretation:** liquid water in snow absorbs radar, so a falling echo over snow is a commonly used sign of surface melt. We did not check it against weather or ground data. NISAR is L-band, which reacts less to wet snow than C-band. New snow, bare ice and debris also change the echo. Five months cannot show long-term glacier loss.
- Glacial lakes: NASA's "High Mountain Asia Near-Global Multi-Decadal Glacial Lake Inventory" version 1 (`HMA_GLI`, NSIDC DAAC), period 2015 to 2018. 12 lakes fall inside the study box.
- Glacier outlines are from OpenStreetMap. The NASA-hosted Randolph Glacier Inventory 7.0 needs an interactive Earthdata login that the script could not complete.

## 5d. Water paths and low ground

- Elevation: NASADEM version 1 (NASA LP DAAC), tiles n27e085 and n28e085, 1 arc-second (about 30 m), measured in February 2000.
- `pipeline/terrain_context.py` fills pits and depressions, then gives every cell a pointer to its steepest downhill neighbour (D8 flow direction, pysheds library).
- "Drop water": the browser follows those pointers from the clicked cell until it reaches the edge of the data. It draws a route and does not simulate water, so there is no volume, depth, speed or time.
- "Low ground": height above the nearest river channel (HAND). Rivers are cells with at least 25 km² of land draining into them. Cells under 10 m and 10 to 20 m above their river cell are shaded. In this box that is 1.3% and 2.1% of the area.
- Limits: NASADEM has metre-scale height errors that grow on steep slopes, and 30 m cells cannot resolve narrow gorges. Treat this as a first look at the terrain. It does not replace a hazard map.

## 6. What is NASA data and what is not

| Used for | Source | NASA? |
|---|---|---|
| All measurements, maps of change, all numbers | NISAR L2 GCOV via ASF DAAC and Harmony | Yes |
| Downhill routes, low ground, glacier height bands | NASADEM v1 via LP DAAC | Yes |
| Glacial lakes | HMA_GLI v1 via NSIDC DAAC | Yes |
| River lines, place names, peak position, glacier outlines | OpenStreetMap | No (open data, credited) |
| Background map | OpenFreeMap | No (open data, credited) |
| 3D terrain and hillshade | Mapzen Terrain Tiles on AWS | No. Could be replaced with NASADEM (NASA). |
| Flood timeline | ICIMOD web page | No (quoted and cited) |

The Space Apps rules require at least one NASA data source and a full list of everything else. Non-NASA data is allowed if it is listed.

## 7. What this cannot tell you

- Radar change is not a damage map. It shows where the surface changed and cannot show what was lost.
- Each period is 12 days. Anything else that happened in those days is included.
- Steep slopes distort radar. The product's mask does not flag those places.
- River lines can sit tens of metres off the real channel.
- NISAR revisits every 12 days per track. It is not a warning system.

## 8. Re-run it

```
python -m venv .venv && .venv\Scripts\activate
pip install -r pipeline/requirements.txt
python pipeline/fetch_gcov_subsets.py            # needs EARTHDATA_TOKEN in .env
python pipeline/fetch_gcov_subsets.py --aoi source
python pipeline/change_detection.py
python pipeline/change_detection.py --raw data/raw/gcov_source
node pipeline/fetch_osm.mjs
python pipeline/river_stats.py
python pipeline/make_tiles.py
python pipeline/make_series.py
python pipeline/fetch_nasa_context.py            # NASADEM and the glacial lake inventory
python pipeline/terrain_context.py
python pipeline/glacier_season.py
python pipeline/build_research_page.py           # turns this file into site/public/research.html
```
