# NISAR — verified notes for "Dancing with the SARs"

Source: the ASF NISAR Data User Guide (https://nisar-docs.asf.alaska.edu/; markdown source at https://github.com/ua-asf/nisar-docs), retrieved 2026-11-14. Coverage counts come from the ASF search API on the same date.

## Mission and data releases (per guide)
- NISAR launched **July 30, 2025**. Its L-band SAR data is public via ASF. S-band data is via ISRO Bhoonidhi.
- Data comes in three maturity levels. Per the guide, **don't casually mix them in one analysis**:

| Maturity | Released | Covers acquisitions | Status | Processing version (CRID) |
|---|---|---|---|---|
| **BETA** | Feb 2026 | Oct 17, 2025 → Jan 20, 2026 (subset) | Not fully calibrated | lower than P05023 |
| **PROVISIONAL** | Jul 20, 2026 | Jun 17, 2026 → ~Oct 23, 2026 | Calibrated, partly validated | P05023 |
| **VALIDATED** | Nov 6, 2026 | Oct 21, 2026 → now | Fully calibrated and validated (levels 0–2) | P05036 |

- **Permanent data gap:** 2026-07-27T22:03:25Z → 2026-08-10T00:55:27Z.
- **SME2 (soil moisture)** exists only as PROVISIONAL, which the guide says "should not be considered fully calibrated". There's no VALIDATED SME2 until 2027.
- Products acquired before Oct 21, 2026 will be reprocessed to VALIDATED in 2027.

## Products most useful for a web app (per guide)

| Product | What it is | Pixel spacing |
|---|---|---|
| **GCOV** (Level 2) | Calibrated backscatter, terrain-corrected (RTC, gamma-0), geocoded to UTM. Real-valued intensity layers such as HHHH and HVHV; extra layers in quad-pol only. Like the RTC/NRB products from other radars. | 10 or 20 m (frequency A), 80 m (frequency B) |
| **GUNW** (Level 2) | Geocoded unwrapped interferogram: surface deformation between two dates | (not checked yet) |
| **GOFF** (Level 2) | Geocoded pixel offsets: larger surface motion | (not checked yet) |
| **SME2** (Level 3) | Soil moisture; accuracy goal 0.06 m³/m³ where vegetation water content < 5 kg/m². Values over dense vegetation and during rain are flagged unreliable; urban areas, permanent water and snow get no value. | 200 m |

## The key enabler: Harmony subsetting (per guide)
- NASA Harmony can extract single layers from GCOV, GUNW, GOFF and SME2 as **Cloud-Optimized GeoTIFFs**.
- It can clip them to our area of interest and reproject them (e.g. EPSG:4326 or UTM).
- This means we **don't have to download full multi-GB HDF5 files**, and we may not need h5py at all.
- Access is through Earthdata Search, the Harmony API, or the `harmony-py` library. All need an Earthdata Login.

## Coverage over Itahari (ASF API, 2026-11-14)
Box: 87.17–87.37°E, 26.58–26.76°N. The search returned 200 products (that's the result cap, so there may be more). Newest product dates:

| Product | Count | Date range |
|---|---|---|
| GCOV | 31 | 2025-11-30 → 2026-11-04 |
| SME2 | 27 | → 2026-10-20 |
| GUNW | 15 | 2026-06-22 → 2026-10-08 |

- Two tracks: 170 (ascending, ~23:30 UTC) and 120 (descending, ~12:50 UTC).
- Example: on track 120, GUNW pairs run 2026-10-08 → 2026-10-20, which is 12 days apart.
- The full listing hasn't been split by maturity yet. **TODO:** count PROVISIONAL vs VALIDATED vs BETA per track.

## GCOV mask meaning (VERIFIED)
Source: NISAR L2 GCOV Product Specification, JPL D-102274 Rev F, v1.5.0 (July 8, 2026), §4.3.3, p. 25.

| Mask value | Meaning |
|---|---|
| `0` | Invalid or partially focused |
| `1`–`5` | Valid; the value is the sub-swath number the majority of samples came from |
| `255` | Fill (outside the image bounds) |

- Dithered-PRF scenes have only one sub-swath, so every valid pixel is `1`.
- **The mask does NOT flag layover or shadow.** The spec text contains no mention of layover. Terrain distortion in the steep Bhote Koshi valley has to be assessed separately (e.g. from a DEM plus the viewing geometry).
- Applies to the 098A scene from 2026-08-19: of 24.68 M pixels in our box, 23.60 M are valid (`1`), 0.35 M are invalid (`0`), and the rest are fill.

## Still UNVERIFIED
- File sizes, and whether Harmony jobs run quickly enough for our deadline.
- Whether every Itahari GCOV is dual-pol (HH+HV), which the "DHDH" mode string in the file names suggests.
- The license and citation wording. The guide's `data-use-citation-guidance` page was a stub when fetched. Check the ASF citation page before submitting.
