# Data quality report: AI adoption in EU enterprises

Run: 2026-11-08 13:35 UTC · Source extract: 2026-11-08T11:57:01+00:00 · Eurostat last update: 2026-06-15

**20 passed · 2 warnings · 0 failed** out of 22 checks.

| Check | Dimension | Rule | Result | Records |
|---|---|---|---|---:|
| C01 | Completeness | Headline AI-use value exists for the EU and all 27 member states in every survey year | ✅ PASS | 0 |
| C02 | Completeness | No missing keys or values in fact tables | ✅ PASS | 0 |
| U01 | Uniqueness | One row per geo, year, size class, indicator and unit (fact_ai_by_size) | ✅ PASS | 0 |
| U02 | Uniqueness | One row per geo, year, sector and indicator (fact_ai_by_sector) | ✅ PASS | 0 |
| V01 | Validity | Every value is a percentage between 0 and 100 | ✅ PASS | 0 |
| V02 | Validity | Years are survey waves 2021, 2023, 2024 or 2025 | ✅ PASS | 0 |
| V03 | Validity | Eurostat flags are from the documented list (b, u, d, bu, e, p) | ✅ PASS | 0 |
| V04 | Validity | Each indicator uses its correct denominator (unit) | ✅ PASS | 0 |
| R01 | Referential integrity | Every indicator, country, sector and size class exists in its dimension table | ✅ PASS | 0 |
| B01 | Consistency | Total (10+ employees) lies between the small, medium and large values | ✅ PASS | 0 |
| B02 | Consistency | Share using any AI >= share using each single AI technology (by size) | ✅ PASS | 0 |
| B03 | Consistency | Share using any AI <= sum of single technologies, where all are published | ✅ PASS | 0 |
| B04 | Consistency | The two source datasets agree on the headline value (cross-dataset) | ✅ PASS | 0 |
| B05 | Consistency | Share using any AI >= share using each single AI technology (by sector) | ⚠️ WARN | 4 |
| B06 | Consistency | EU average lies within the range of its member states | ✅ PASS | 0 |
| A01 | Plausibility | Year-on-year change in headline AI use larger than 12 pp (review) | ⚠️ WARN | 5 |
| X01 | Accuracy | Loaded row counts and value totals match the extract control totals | ✅ PASS | 0 |
| X02 | Accuracy | EU 2025 headline matches the 20.0% published by Eurostat | ✅ PASS | 0 |
| F01 | Timeliness | Source data is not older than the next scheduled Eurostat release | ✅ PASS | 0 |
| L01 | Lineage | Every raw source row is accounted for: kept + out of scope + not published = raw | ✅ PASS | 0 |
| L02 | Lineage | Committed data files are byte-identical to the extract (SHA-256 fingerprint) | ✅ PASS | 0 |
| L03 | Lineage | Figures in the published report reconcile to the warehouse tables | ✅ PASS | 0 |

## Findings to review

**A01** (5 records)
- DK 2024: 12.4 pp vs previous wave
- DK 2025: 14.5 pp vs previous wave
- FI 2025: 13.4 pp vs previous wave
- LT 2025: 12.5 pp vs previous wave
- SE 2024: 14.7 pp vs previous wave

**B05** (4 records)
- RS 2024 sector C27: any AI 1.57 < single technology 1.89
- RS 2024 sector G45: any AI 0.67 < single technology 0.83
- RS 2024 sector I55: any AI 0.43 < single technology 0.54
- RS 2024 sector N79: any AI 20.93 < single technology 21.59

## Lineage

| Table | Raw rows | Kept | Out of scope | Not published (of which confidential) | Source SHA-256 |
|---|---:|---:|---:|---:|---|
| fact_ai_by_size | 72,527 | 26,963 | 44,927 | 637 (239) | `411ffabeb5bf797e…` |
| fact_ai_by_sector | 684,190 | 47,700 | 627,809 | 8,681 (2,985) | `d6268c99064d0370…` |
