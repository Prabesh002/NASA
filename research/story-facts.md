# Story fact pack: Rasuwa flood, 26 Aug 2026

**For the user to write the story in their own English.** This is raw material only: facts and sources, ordered along the river from source to downstream. Claude does not write the narrative; the user does.

Status tags:
- ✅ verified verbatim from the source
- 🟡 from a summary of the source (read the original before using)
- 📡 our own NISAR measurement (filled in once processing is done)

## 0. Numbers you must quote with source + date (they differ between sources)
- 🟡 Deaths: 1,259 per UNOCHA Situation Report No. 6 (as of 3 Sep 2026); more than 1,400 per British Red Cross. → https://www.unocha.org/publications/report/nepal/nepal-rasuwa-flood-situation-report-no-6-3-september-2026 · https://www.redcross.org.uk/stories/disasters-and-emergencies/world/nepal-flash-floods-2026
- 🟡 5,083 out of contact; 3,844 displaced in 34 sites (UNOCHA, 3 Sep).
- 🟡 84,270 people affected across 17 municipalities in 6 districts: Rasuwa, Nuwakot, Dhading, Chitwan, Gorkha, Tanahu (UNDP). → https://www.undp.org/asia-pacific/nepal-floods-2026

## 1. The source: Langtang Lirung → Lhende Khola
- ✅ ICIMOD: a "very large slab of rock and glacier ice broke away" from the **north face of Langtang Lirung** (7,227 m), "shortly after 8:37 am".
- ✅ ICIMOD: it "fell around 1200 metres into the valley of the Lhende Khola, a stream that marks the border". The failure zone was at 5,000–5,500 m.
- ✅ ICIMOD: "The USGS places the failure inside Langtang National Park." Early reports said the flood came from Tibet because the Lhende's headwaters are in Gyirong County.
- ✅ ICIMOD: scientists describe it as an "ice-rock avalanche … that turned into a debris flow".
- ✅ Wikipedia (citing USGS): the collapse itself produced a seismic signal, Ms 5.2, at 02:52 UTC (08:37 NPT). ⚠️ The Kathmandu Post reported a USGS "magnitude 4.4 earthquake". The magnitudes conflict.
- 🟡 IRDR analysis (Adhikari et al., via ICIMOD): the failure may have happened on the **afternoon of 25 Aug**, with debris damming the river for 18–19 hours before it burst. This is an open question.
- 📡 NISAR source zone (track 98, 19 -> 31 Aug, HH): a continuous band of strong change (beyond +-3 dB, both rises and falls) starts about 3.5 km north of the Langtang Lirung summit (head of the band read off the map at about 28.289N 85.525E, +-200 m; summit per OSM 28.2564N 85.5167E) and runs north-west down a tributary valley. OSM names along the traced drainage: (unnamed stream) > Chhochen Khola > Chusumdo Tsangpo > Lende Khola. **This position is consistent with ICIMOD's "north face of Langtang Lirung"; the radar does not show what the material was or when in the 12 days it moved.**
- 📡 Along the first 11.6 km (source to the junction with the Lende Khola): 36% of pixels within 100 m of the OSM stream line changed by more than 3 dB (HH; 30% in HV). In the 7 ordinary 12-day steps on the same track (Jun 20 - Oct 18) the same stretch had 0.1-3.5% (median 0.4%).
- 📡 The upper Lende Khola (the 12 km coming from the north, above that junction; the direction of the Tibetan headwaters) shows **no** unusual change in the flood step: 0.2% of pixels, inside its ordinary range of 0.1-1.9%. So in the radar data the change enters the Lende from the Langtang Lirung side tributary, not from the north.
- ⚠️ High, steep, snowy ground changes radar brightness for many reasons (snowfall, melt, layover). Scattered red/blue speckle on the high slopes is not the flood.

## 2. A dam that burst? (disputed)
- ✅ Kathmandu Post quotes DHM's Binod Parajuli: "An ice and debris lake formed and then burst."
- ✅ ICIMOD: "On 26 August, there was no lake found at the origin point." If debris blocked the Lhende temporarily, that counts as a "landslide-dam outburst stage", not a classic GLOF.
- ✅ Kathmandu Post: per satellite imagery Chinese authorities shared with DHM, the blockage was "about 20 kilometres upstream of the Miteri Bridge".

## 3. Rasuwagadhi / Gyirong border crossing
- ✅ ICIMOD: debris met the Bhotekoshi "at the Rasuwagadhi–Gyirong border crossing".
- ✅ ICIMOD: Rasuwagadhi and Timure were "the worst hit".
- 🟡 Wikipedia: the flood destroyed Gyirong Port.
- 📡 Lende Khola from the tributary junction to Rasuwagadhi (km 11.6-20.7 of the traced path): 19% of pixels within 100 m changed by more than 3 dB (HH; 24% HV). Ordinary steps: 1.2-5.7% (median 1.5%).
- 📡 Rasuwagadhi and the first 5 km below it (km 20.7-25.7, includes the Timure reach): 13% (HH; 12% HV). Ordinary steps: 0.4-5.3% (median 2.7%).
- 📡 Control, Kyirong Tsangpo (the main river arriving from Tibet, 14 km above the confluence): 3.8% in the flood step, against 1.0-3.7% in ordinary steps. That is at the top of its ordinary range, not clearly above it. Note its last few hundred metres lie within 100 m of the flood channel.

## 4. The warning minutes (key for the evacuation theme)
- ✅ ICIMOD (read 14 Nov 2026, snapshot `research/snapshots/icimod.txt`): "Reported arrival times in the upper corridor recorded at 8:40 am in Rasuwagadhi and at 9:20 am in Betrawati, suggest a speed of 20 m/s (or 72 km/h) as both locations are 56 km apart. Some scientists consider this implausible for a channelised flow."
- ✅ ICIMOD: "While there was no warning for Rasuwagadhi and Timure, Nepal's Department of Hydrology and Meteorology's Flood Forecasting Division sent SMS alerts to around 679,000 people in Rasuwa, Nuwakot, Dhading and Chitwan at 9:15-9:16 am, about ten minutes after the surge entered the Bhotekoshi and at least fifteen minutes after Timure was under water. Those alerts helped further downstream: Malekhu was not reached until after 11:00, more than two hours later."
- ✅ ICIMOD: "Why the 28-minute gap between the seismic signal at 8:37 and hydrologists learning of the flood at 9:05?" ... "Twenty-eight minutes to a confirmed alert is not slow by regional standards; the problem is that the flood reached the nearest settlements faster than any plausible detection time." 
- ✅ Wikipedia: "At 09:00, the Nepalese Department of Hydrology and Meteorology was informed". This slightly differs from the 9:05 above.

## 5. Timure → Syabrubesi → Betrawati
- ✅ ICIMOD: the flow went "down the Bhotekoshi and Trishuli through Timure, Syabrubesi, Betrawati and beyond".
- 🟡 Rasuwagadhi to Betrawati is about 56 km (ICIMOD summary).
- 🟡 Syabrubesi hydropower projects were damaged (Kathmandu Post headline: https://kathmandupost.com/national/2026/08/26/major-flood-damages-syabrubesi-hydropower-projects-in-rasuwa).
- 📡 Below Timure to just past Syabrubesi (km 25.7-37): 14% (HH; 12% HV). Ordinary steps: 0.9-6.4% (median 1.4%).
- 📡 Syabrubesi to Betrawati (km 37-66.3): 19% (HH; 14% HV). Ordinary steps: 0.8-3.6% (median 1.3%). The strongest part of this stretch is the last 6 km above Betrawati (30-50% per 500 m bin).
- 📡 Whole traced path, source to Betrawati (66.3 km along OSM lines; Rasuwagadhi at km 20.7, Syabrubesi km 35.0): 20.7% of 129,965 pixels in the flood step (HH), mean absolute change 1.92 dB. The other seven 12-day steps: 0.8-3.8%, mean absolute change 0.60-1.14 dB.
- 📡 Controls in the flood step: Langtang Khola 0.2%, Chilime Khola 0.7%, upper Lende Khola 0.2% (all inside their own ordinary ranges).
- 📡 The two steps after the flood (31 Aug -> 12 Sep: 3.7%; 24 Sep -> 6 Oct: 3.8%) are the highest of the ordinary steps. The second one is scene-wide (controls rise too, and the whole image is about 0.6 dB darker), so it looks like a weather or season effect rather than the river.
- 📡 Other tracks: track 48 (16 -> 28 Aug) and track 149 (23 Aug -> 4 Sep) also show the change band, from other viewing directions. Their before/after scenes use different radar modes, so we only show them as maps and take no numbers from them.
- ⚠️ Our river distance Rasuwagadhi-Betrawati is 45.6 km along OSM lines; ICIMOD says the two are "56 km apart". We did not resolve the difference (road distance? different line?). Quote each with its source.

## 6. Further downstream
- ✅ Wikipedia: the flood "struck dozens of settlements along a 72 km … stretch of the Trishuli River", and some victims were carried "250 km … into neighbouring India".
- 🟡 Galchhi gauge, about 100 km downstream (ICIMOD), rose again on 30 Aug.
- Flood warnings were issued for Rasuwa, Nuwakot, Dhading, Gorkha and Chitwan (Wikipedia).

## 7. What NISAR is, and what it can and can't do (for the "how we know" part)
- ✅ NISAR is a NASA–ISRO radar satellite, launched 30 Jul 2025. Radar works through cloud and at night (ASF NISAR User Guide).
- ✅ Over this corridor the data shows passes on Aug 16, 19, 23, 28, 31 and Sep 4, 2026. That's a look every 3–5 days across 3 tracks (ASF archive).
- ✅ It is **not** an early-warning system. Each track repeats every 12 days, and processing adds delay. It shows what changed and where, after the fact.
- ✅ The July 2025 Miteri Bridge flood happened **before** NISAR launched, so there is no NISAR data of it.

Full sources and caveats: `research/rasuwa-flood-2026.md`, `research/nisar-notes.md`.

## 8. How the 📡 numbers were made (so you can explain them)
- Radar: NISAR L2 GCOV provisional, track 98 ascending, HH unless noted. Change = 10 log10(after/before) after a 5x5-pixel average (10 m pixels).
- "X% changed by more than 3 dB" = share of valid pixels within 100 m of the OpenStreetMap river line whose change is beyond +3 or -3 dB.
- "Ordinary steps" = the same calculation for the seven other 12-day steps between 20 Jun and 18 Oct 2026 (the 26 Jul -> 19 Aug step is skipped: mission data gap, 24 days).
- Scripts: `pipeline/change_detection.py`, `pipeline/river_stats.py`. Output: `site/public/data/river_stats.json`.
- Limits: change is not damage; 12 days of everything is included; steep slopes distort the signal; OSM lines can be tens of metres off; data are provisional.
