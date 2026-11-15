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

SI draft written 2026-11-15 at the user's request (Claude Opus 5.5). Review it and change it to your own words before pasting:

> I built an interactive story map of the flood that hit Rasuwa, Nepal, on 26 August 2026, using radar from the NASA–ISRO NISAR satellite. A slab of rock and ice fell from Langtang Lirung, and the flood ran down the Lende Khola, Bhotekoshi and Trishuli past Rasuwagadhi, Timure, Syabrubesi and Betrawati. I compared NISAR passes from before and after the flood and mapped where the ground changed.
>
> The radar shows the flood path clearly. About 1 in 5 patches of ground beside the river changed strongly (20.7% by more than 3 dB). In a normal 12 days it is about 1 in 80 (median 1.25% over seven ordinary periods). Four neighbouring rivers showed no such jump on the same dates. On the site you can follow the flood from its source to Betrawati, compare it with a normal 12 days, click any spot to see its radar record over ten dates, look at the glaciers above the valley, and trace where water runs downhill on NASA elevation data.
>
> This matters because the flood reached Rasuwagadhi and Timure before any warning went out (ICIMOD). The site is written in plain English for residents and local government: it shows where the water went and links to Nepal's official flood and disaster agencies. It is a prototype built on provisional data, and the site explains its limits.

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

SI draft written 2026-11-15 at the user's request (Claude Opus 5.5). Review and edit before pasting:

> **What it does.** The site follows the 26 August 2026 Rasuwa flood down the valley, from the source below Langtang Lirung, along the Lende Khola, Bhotekoshi and Trishuli, past Rasuwagadhi, Timure and Syabrubesi to Betrawati, 66 km downstream. At each stop the map shows where NISAR radar saw the ground change across the flood, with a short note and its sources. You can:
> - slide between the flood 12 days and a normal 12 days to see the difference
> - play the flood down the valley with the times ICIMOD reported
> - click any spot to see its radar record over ten dates (20 June to 18 October) and download it as a CSV
> - step through the summer to see that only the flood period lights up
> - look at radar change on the glaciers above the valley and the glacial lakes from NASA's HMA_GLI inventory
> - click anywhere to trace where water runs downhill, using NASA's NASADEM elevation model
>
> **How it works.** I downloaded NISAR L2 GCOV radar (provisional release, via NASA Harmony and the ASF DAAC) for three satellite tracks. For each pair of passes 12 days apart, I measured the change in radar echo (log-ratio in decibels). Along the traced river path, 20.7% of ground within 100 m of the river changed by more than 3 dB in the flood period, against a median of 1.25% in seven ordinary periods; near the source it reaches 88%. Four neighbouring rivers outside the flood path showed no such jump. All processing runs offline in Python scripts that log every source URL. The results are turned into map tiles and served as a static website on Cloudflare Workers.
>
> **Benefits and intended impact.** ICIMOD reports that there was no warning for Rasuwagadhi and Timure. The site is written in plain English for residents and local government, to show where the water went, and it links to Nepal's official agencies (DHM, NDRRMA, BIPAD). Radar sees through cloud and works at night, which matters in the monsoon. The same steps could be repeated for another valley after the next flood.
>
> **Creativity.** Instead of a single before/after picture, every result is shown against a normal 12 days, so a non-expert can see what "unusual" looks like. The story moves down the river the way the flood did, and any point on the map can be clicked to see its own radar history.
>
> **Factors we considered.** The NISAR data is provisional. Steep slopes distort radar. One track switches imaging mode between dates, so I used the cleanest pair (track 98 ascending). Change is not the same as damage, and 12 days includes everything that happened in that time. River lines from OpenStreetMap can be tens of metres off. The site does not invent evacuation routes or safe zones. All these limits are shown on the site's method page.
>
> **Tools.** Python (rasterio, NumPy, Pillow, harmony-py, pysheds), JavaScript, HTML, CSS, Node.js, MapLibre GL JS 4.7.1, Cloudflare Workers static assets and Wrangler, headless Chrome for the slide clips. No hardware. SI (Claude by Anthropic, through Claude Code) was used for research, coding, data processing and writing; details are at https://nasa.nesomotions.com/si-usage.html

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
