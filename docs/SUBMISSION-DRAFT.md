# Submission sheet (draft for the Space Apps project form)

Deadline: **Sunday 15 Nov 2026, 23:59 Nepal time.** Click **"Submit for Judging"**; saving alone is not enough.
You can resubmit until the deadline; the last saved submission is judged.

Fields marked **YOU** must be in your own words (SI may not come up with the idea or the story).
Fields marked FACTS are lists you can paste and edit.

## 1. Project name: YOU
The site currently shows a working title ("The Rasuwa flood, traced from space by radar"). Replace it in
`site/public/index.html` (`<title>`, `<h1>`) with your own.

## 2. High-level summary: YOU
Facts you may want to draw on (all from `research/story-facts.md`, with sources there):
- What it is: an interactive story map of the 26 Aug 2026 Rasuwa flood, from source to Betrawati.
- NASA data at the core: NISAR radar, 12 scenes, change detection between passes.
- Main result: along the traced 66 km river path, 20.7% of ground within 100 m of the river changed by
  more than 3 dB across the flood step; 0.8-3.8% in seven ordinary 12-day steps; control rivers stayed
  in their ordinary range.
- The change enters the Lende Khola from the Langtang Lirung side, not from the north.
- Audience and purpose: yours to state.

## 3. Demo link: YOU (video of 30 s or less, or 7 slides or fewer; English; public, no login)
Going over the limit makes the project ineligible for global judging. A screen recording of the site
scrolling from the source to Betrawati fits in 30 s. If SI generates any image or video for it, it needs a
visible watermark; a plain screen recording of the site does not.

## 4. Final project link
https://nasa.nesomotions.com  (must be public, no login; check in a private window after deploying)

## 5. Project details: YOU, with these FACTS
- What it does: scroll story with a 3D map; radar change overlay; layer panel (three NISAR tracks, HH and
  HV, before/after radar images, ordinary 12-day steps); river profile strip that doubles as navigation;
  "How we know" panel with baseline and control rivers; links to DHM, BIPAD and NDRRMA.
- How it works: offline Python pipeline (NASA Harmony subsets -> log-ratio change -> river statistics ->
  web tiles), static site on Cloudflare Workers, MapLibre GL JS in the browser.
- Tools and languages: Python (rasterio, NumPy, Pillow, harmony-py), JavaScript, HTML, CSS, Node.js,
  MapLibre GL JS 4.7.1, Cloudflare Workers static assets, Wrangler.

## 6. NASA data and resources used: FACTS
- NISAR L2 GCOV, provisional release (collection C2854338529-ASF, CRID P05023), NASA/JPL and ISRO,
  distributed by the Alaska Satellite Facility DAAC. Tracks 98A (10 dates, 20 Jun - 18 Oct 2026),
  48D (16 and 28 Aug), 149D (23 Aug and 4 Sep).
- NASA Harmony (subsetting service): https://harmony.earthdata.nasa.gov/
- NASA Common Metadata Repository (granule search): https://cmr.earthdata.nasa.gov/
- ASF Data Search Vertex: https://search.asf.alaska.edu/
- NISAR Data User Guide (ASF): https://nisar-docs.asf.alaska.edu/
- NISAR L2 GCOV Product Specification, JPL D-102274 Rev F.

## 7. Space Agency Partner data: FACTS
- ISRO: NISAR is a joint NASA-ISRO mission. (We used the L-band data distributed by NASA/ASF. We did not
  use ISRO's S-band data.)

## 8. References: FACTS
- ICIMOD, Kyirong-Rasuwa flood 2026: https://www.icimod.org/kyirong-rasuwa-flood-2026-nepal-china-border/
- The Kathmandu Post, 26 Aug 2026:
  https://kathmandupost.com/national/2026/08/26/ice-avalanche-debris-lake-may-have-triggered-bhotekoshi-flood
  https://kathmandupost.com/national/2026/08/26/major-flood-damages-syabrubesi-hydropower-projects-in-rasuwa
- OpenStreetMap contributors (ODbL 1.0), via the Overpass API.
- OpenFreeMap basemap (OpenMapTiles schema): https://openfreemap.org/
- Mapzen Terrain Tiles on AWS Open Data: https://registry.opendata.aws/terrain-tiles/  (URL not re-checked; verify)
- MapLibre GL JS 4.7.1 (BSD-3-Clause): https://maplibre.org/
- Fonts: Archivo and Source Serif 4 (SIL Open Font License), Google Fonts.
- Official agency links shown on the site: https://www.dhm.gov.np/ , https://hydrology.gov.np/ ,
  https://bipadportal.gov.np/ , https://ndrrma.gov.np/
- Add anything you cite in your own story text (UNOCHA, UNDP, Red Cross, Wikipedia), after reading the originals.

## 9. SI usage: FACTS (edit to match what you actually did)
We used Claude (Anthropic) through Claude Code as a tool. SI was not used to come up with the idea: the
challenge, the Rasuwa flood study area, the audience and the approach (trace the flood to its source and
make it usable for residents) were chosen by the team, and the story text is written by the team.
SI was used to: collect and summarise the official rules and data documentation; find NISAR scenes;
write the data-processing code and the website code (each file is marked in its header); compute the
derived change maps and statistics with that code; write interface labels, data captions and the method
and limits notes; choose the visual design. No SI-generated images, video or audio are used. No NASA
branding is used. Full log: docs/SI-USAGE.md; public statement: https://nasa.nesomotions.com/si-usage.html

## Before you submit
- [ ] Story text filled in (`site/public/index.html`, search for `USER TEXT`), then `npx wrangler deploy`.
- [ ] Site opens in a private window with no login.
- [ ] Demo is 30 s or less (or 7 slides or fewer), English, public link.
- [ ] Registration: Ithari local event, accepted (not waitlisted), challenge "Dancing with the SARs".
- [ ] Optional: request a FortiGuard web filter classification for the new domain (Submission Guide tip).
- [ ] Clicked "Submit for Judging".
