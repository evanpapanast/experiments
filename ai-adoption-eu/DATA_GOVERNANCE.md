# Data governance: AI adoption in EU enterprises

How this dataset is sourced, controlled, checked and published. The aim is that anyone can trace every
number in the report back to the official source and see which checks it passed on the way.

**Latest data quality run:** [data_quality/dq_report.md](data_quality/dq_report.md)

## 1. Ownership and access

| | |
|---|---|
| Data owner (source) | Eurostat, *ICT usage and e-commerce in enterprises* survey |
| Data steward (this project) | Evangelos Papanastasis |
| Licence | Eurostat re-use policy: free re-use with attribution (Commission Decision 2011/833/EU) |
| Personal data | None. All figures are aggregated percentages of enterprises; no individuals or single companies |
| Confidential data | Eurostat suppresses values that could reveal single enterprises (flag `C`). These are **excluded**, never estimated |
| Warehouse access | BigQuery project is private to the owner (Google Cloud IAM). Only aggregated outputs are published |
| Public outputs | Code, tidy CSVs, the report and the data quality report on GitHub |

## 2. Lineage: from source to report

```
Eurostat API ─► raw/ (not committed) ─► data/*.csv ─► BigQuery tables ─► reporting views ─► dashboard/data.js ─► report
   (1)               (2) SHA-256           (3) SHA-256    (4) control totals   (5) same SQL       (6) reconciled
```

1. **Source:** two Eurostat datasets downloaded from the official API. The URL and the "last update" timestamp Eurostat stamps on each row are recorded.
2. **Raw fingerprint:** a SHA-256 hash of each raw file is stored in [`data/manifest.json`](data/manifest.json). If Eurostat silently revises the data, the hash changes.
3. **Row reconciliation:** every raw row is classified as *kept*, *out of scope* (indicator not used) or *not published* (missing or confidential). The three must add up to the raw total (check L01).
4. **Control totals:** row counts and value totals of each output file are written to `load_control_totals` in BigQuery. After loading, the warehouse must match them exactly (X01).
5. **One version of the logic:** the reporting views are written once (`sql/02_marts.sql`) and run unchanged in BigQuery and locally, so the published report and the warehouse cannot drift.
6. **Report reconciliation:** the numbers inside the published report are compared again with the warehouse tables (L03).

## 3. Data quality framework

22 automated checks, grouped by the standard data quality dimensions. Each has a severity:

- **FAIL**: the data must not be published until fixed. The check script exits with an error, which blocks the publish.
- **WARN**: publish, but review. Used for known source issues and unusual movements that may well be real.

| Dimension | What it protects against | Checks |
|---|---|---|
| Completeness | Missing countries or years; empty fields | C01, C02 |
| Uniqueness | Double counting from duplicate rows | U01, U02 |
| Validity | Impossible values (outside 0–100%), unknown years or flags, wrong denominators | V01–V04 |
| Referential integrity | Codes with no description, e.g. a country not in the country list | R01 |
| Consistency | Numbers that contradict each other: total vs size classes, "any AI" vs single technologies, two source files disagreeing, EU average outside the member-state range | B01–B06 |
| Plausibility | Suspicious jumps between survey waves (> 12 pp) | A01 |
| Accuracy | Load incomplete; headline differs from Eurostat's published figure | X01, X02 |
| Timeliness | Eurostat has published a newer release than the one used | F01 |
| Lineage | Rows lost or invented in the transformation; files changed after extraction; report not matching the warehouse | L01–L03 |

Tolerances: 0.05 percentage points for consistency rules, which absorbs Eurostat's 2-decimal rounding. Comparisons
use tolerances rather than exact equality because computers store decimals approximately (19.95 is stored as 19.9499…).

**Where the checks run**

| | Local (Python + SQLite) | BigQuery |
|---|---|---|
| Command | `python scripts/03_data_quality.py` | run `sql/04_data_quality_checks.sql` |
| Checks | All 22 | The 19 SQL checks (lineage checks need the files) |
| Output | `data_quality/dq_report.md`, report page | views `dq_results`, `dq_failures`; audit table `dq_log` |
| Audit trail | Git history of the report | `dq_log`: one row per check per run, with timestamp |

**Proof that the checks work.** Before publishing, the gate was tested by deliberately corrupting a copy of the
data: a duplicate row, a value of 120%, a deleted headline value, a wrong value for Poland and an unknown country code.
All five were caught, most by several independent checks, and the gate blocked the publish.

## 4. Known issues in the source (current findings)

| Check | Finding | Decision |
|---|---|---|
| B05 | Serbia 2024, 4 sectors: the share using "any AI" is lower than the share using one specific technology, which is logically impossible | Kept as published and flagged as a warning, because correcting official statistics ourselves would break lineage. Serbia is not an EU member; its values appear only if a user selects Serbia. Worth reporting to Eurostat |
| A01 | Large jumps between waves in 2024–2025 for Denmark, Sweden, Finland and Lithuania (+12 to +15 pp) | Reviewed: no break-in-series flag, and the pattern matches the generative-AI uptake across the EU. Accepted as real |
| (lineage) | 239 values in `isoc_eb_ai` and 2,985 in `isoc_eb_ain2` are confidential; others are simply not published | Excluded, never imputed. Charts show only published values |
| (flags) | Some values carry Eurostat flag `b` (break in time series) | Kept and shown with an asterisk and tooltip in the report |

## 5. Change management

- Everything is version-controlled in Git: code, SQL, data files and the data quality report. Any change to a number shows up as a visible diff.
- To refresh: run the extract (1), the data quality gate (3), rebuild the report (2). Publish only if the gate passes.
- The data dictionary is in [DATA_DICTIONARY.md](DATA_DICTIONARY.md).
