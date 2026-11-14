# Rasuwa (Bhote Koshi–Trishuli) flood, Aug 2026 — facts and NISAR coverage

Compiled 2026-11-14. **Casualty and impact figures differ between sources. Always quote them with source and "as of" date. Never merge or round them into a single "fact".**

## There are two different Rasuwa floods. Don't confuse them.

| Event | Date | NISAR coverage? |
|---|---|---|
| Lhende/Bhote Koshi flood that destroyed the **Miteri Bridge** and damaged Rasuwagadhi dry port | **July 8, 2025** (per news search summary; e.g. [Himalayan Times](https://thehimalayantimes.com/environment/glof-confirmed-as-the-reason-for-rasuwa-flood), [BorderLens](https://www.borderlens.com/2025/07/23/climate-crisis-at-nepals-doorstep-rasuwa-flood-signals-a-growing-himalayan-threat/)) | **No.** NISAR launched July 30, 2025, after this flood. |
| **Kyirong–Rasuwa flood**, Bhote Koshi → Trishuli corridor | **Reported around Aug 26, 2026** ([Kathmandu Post, 2026-08-26](https://kathmandupost.com/national/2026/08/26/major-flood-damages-syabrubesi-hydropower-projects-in-rasuwa)). Exact date and time are **UNVERIFIED**; confirm from the UNOCHA reports. | **Yes.** See below. |

## Aug 2026 event: what sources say (search summaries; read the originals before quoting)
- **Cause is disputed.** It's described as a rock-ice or ice avalanche plus a debris-dammed lake rather than a classic GLOF. A GLOF had not been conclusively confirmed. Sources:
  - [ICIMOD](https://www.icimod.org/kyirong-rasuwa-flood-2026-nepal-china-border/)
  - [Kathmandu Post: "ice avalanche debris lake may have triggered bhotekoshi flood"](https://kathmandupost.com/national/2026/08/26/ice-avalanche-debris-lake-may-have-triggered-bhotekoshi-flood)
  - [Wikipedia: 2026 Nepal floods](https://en.wikipedia.org/wiki/2026_Nepal_floods)
- **UNOCHA Situation Report No. 6 (as of 3 Sep 2026)** ([link](https://www.unocha.org/publications/report/nepal/nepal-rasuwa-flood-situation-report-no-6-3-september-2026)), per the search summary: 1,259 dead, 5,083 out of contact, 3,844 displaced in 34 sites. **Verify these against the report itself.**
- **Red Cross UK** ([link](https://www.redcross.org.uk/stories/disasters-and-emergencies/world/nepal-flash-floods-2026)), per the search summary: more than 1,400 dead.
- **UNDP** ([link](https://www.undp.org/asia-pacific/nepal-floods-2026)), per the search summary: 84,270 people affected across 17 municipalities in 6 districts (Rasuwa, Nuwakot, Dhading, Chitwan, Gorkha, Tanahu).
- **Wikipedia**, per the search summary: damage along a ~72 km stretch of the Trishuli, plus the Gyirong border port.

## Origin and sequence (sourced; read the originals before quoting; the conflicts are kept as-is)
Sources checked 2026-11-14:
- ICIMOD: https://www.icimod.org/kyirong-rasuwa-flood-2026-nepal-china-border/
- Kathmandu Post: https://kathmandupost.com/national/2026/08/26/ice-avalanche-debris-lake-may-have-triggered-bhotekoshi-flood
- Wikipedia (redirects to "2026 Nepal–Tibet floods"): https://en.wikipedia.org/wiki/2026_Nepal_floods

**Origin**
- ICIMOD: a slab of rock and glacier ice broke from **the north face of Langtang Lirung** (a 7,227 m peak in Rasuwa, near the China border).
- It fell about 1,200 m into the **Lhende Khola** valley, a border stream. The failure zone was at 5,000–5,500 m.
- ICIMOD notes early reports said the flood came from Tibet because the Lhende's headwaters are in Gyirong County. The USGS places the failure inside Langtang National Park, on the Nepal side.

**Timing**
- ICIMOD and Wikipedia: about **08:37 NPT, 26 Aug 2026** (02:52 UTC). The collapse itself generated a seismic signal (Wikipedia citing USGS: Ms 5.2).
- **Conflicts:**
  - The Kathmandu Post reports a USGS "magnitude 4.4 earthquake" at 8:37 am.
  - An IRDR analysis (Adhikari et al., per the ICIMOD summary) puts the failure on the **afternoon of 25 Aug**, with debris damming the river for 18–19 h before it burst.

**Sequence (sources differ in detail)**
1. Rock-ice avalanche, which became a debris flow.
2. Possible temporary dam of the Lhende Khola. The Kathmandu Post quotes DHM's Binod Parajuli: "An ice and debris lake formed and then burst". ICIMOD says no lake was present at the origin point on 26 Aug.
3. Confluence with the Bhotekoshi at Rasuwagadhi–Gyirong.
4. Down the Bhotekoshi and Trishuli through Timure, Syabrubesi, Betrawati and beyond. ICIMOD: Rasuwagadhi and Timure were "the worst hit".

**Early warning timeline (per ICIMOD summary)**
- 8:40 am: water at Rasuwagadhi
- 9:05: hydrologists informed
- 9:15: SMS alerts

**Location**
- Wikipedia infobox coordinates: ~28.3°N 85.5°E.
- Exact coordinates of the failure scar are **UNVERIFIED**. Locate them in the radar data or an official map; don't invent them.

## NISAR acquisitions over the corridor (ASF API, 2026-11-14)
Search box: 85.10–85.50°E, 27.85–28.40°N (Rasuwagadhi/Timure → Syabrubesi → toward Betrawati). Three independent tracks bracket the event. **All the bracketing scenes are PROVISIONAL (CRID P05023)**, so the processing is consistent across them.

| Track | Last scene before ~Aug 26 | First scene after | Change pair spanning the event (GUNW/GOFF) |
|---|---|---|---|
| 048 descending (~12:58 UTC) | 2026-08-16 | 2026-08-28 | 0816 → 0828 |
| 098 ascending (~23:39 UTC) | 2026-08-19 | 2026-08-31 | 0819 → 0831 |
| 149 descending (~13:06 UTC) | 2026-08-23 | 2026-09-04 | 0823 → 0904 |

- **GCOV (backscatter):** 61 products from Jun 8 to Nov 8, 2026, roughly one every 12 days per track. The data switches to VALIDATED (P05036) from 2026-10-22, so don't mix it naively with PROVISIONAL.
- **GUNW and GOFF (deformation and offsets):** 45 pairs each.
- **SME2 (soil moisture):** 45 products, PROVISIONAL only, not fully calibrated.
- **Data gap:** Jul 27 → Aug 10, 2026 (mission-wide).
- Some dates have two or more products with or without a CRID. These may be duplicates or BETA reprocessing; **check before using**.

## Known risks (to verify with the actual data)
- **Steep Himalayan terrain** causes SAR layover and shadow. GCOV includes a mask layer; check how much of the valley floor is usable on each track. **UNVERIFIED.**
- **Narrow river vs 10–20 m pixels:** whether channel changes are resolvable is **UNVERIFIED** until we look at actual subsets.
- **Sensitivity:** this is a deadly disaster. Use a respectful tone, cite sources, and no sensational or SI-generated imagery of victims or damage.
