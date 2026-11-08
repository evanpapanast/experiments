# AI adoption in EU enterprises

**[Open the interactive report →](https://evanpapanast.github.io/experiments/ai-adoption-eu/dashboard/)**

How many European companies use artificial intelligence, what they use it for, what holds the others back,
and which sectors and countries lead. Built on official Eurostat survey data, modelled in Google BigQuery
and presented as a Power BI-style interactive report.

## Key findings (2025, enterprises with 10+ employees)

| | |
|---|---|
| **EU adoption** | 20.0% of enterprises use AI, up from 7.7% in 2021 and 13.5% in 2024 |
| **Leaders** | Denmark 42.0%, Finland 37.8%, Sweden 35.0% |
| **Austria** | 30.0%, ranked #7 of 27 (from 8.8% in 2021) |
| **Size gap is widening** | Large firms 55.0% vs small firms 17.0% (EU). The gap grew from 22 pp in 2021 to 38 pp |
| **Top use** | Marketing and sales (34.7% of AI users); finance and controlling 23.1% |
| **Top barrier** | Lack of expertise, cited by 70% of firms that considered AI but did not adopt it |
| **Sectors** | IT services 65.7% and R&D 52.1% lead; construction 10.8% trails. Pharma: 41.3% |

## Pipeline

```
Eurostat API ──► Python (extract & tidy) ──► Google BigQuery ──► SQL reporting views ──► Data quality gate ──► HTML report
  isoc_eb_ai       scripts/01_...py           star schema          sql/02_marts.sql        22 checks             dashboard/
  isoc_eb_ain2     + lineage manifest         2 facts + 4 dims                             sql/04, scripts/03
```

| Layer | What it does | Files |
|---|---|---|
| Extract & tidy | Downloads both datasets and Eurostat code lists, keeps 31 indicators, writes long-format CSVs | `scripts/01_extract_transform.py` → `data/` |
| Warehouse | BigQuery dataset `ai_adoption`: `fact_ai_by_size`, `fact_ai_by_sector`, `dim_indicator`, `dim_geo`, `dim_sector`, `dim_size_class` | `sql/00_create_tables.sql`, `sql/01_load_dimensions.sql` |
| Business logic | Four reporting views: country adoption with EU rank and change, size gap, AI profile (uses, technologies, barriers, sourcing), sector adoption | `sql/02_marts.sql` |
| Control totals | Expected rows, value totals and source dates per table, generated at extract time | `sql/03_load_control_totals.sql`, `data/manifest.json` |
| Data quality | 22 checks across completeness, uniqueness, validity, referential integrity, consistency, plausibility, accuracy, timeliness and lineage. FAIL blocks publishing; results logged in BigQuery (`dq_log`) | `sql/04_data_quality_checks.sql`, `scripts/03_data_quality.py` → [`data_quality/dq_report.md`](data_quality/dq_report.md) |
| Report | Runs the **same SQL** locally (SQLite) to build the report dataset, then a dependency-free HTML/SVG report | `scripts/02_build_marts.py`, `dashboard/` |

The reporting SQL is written once and runs unchanged on BigQuery and locally, so the report can be rebuilt
without cloud access and both outputs reconcile to the cent.

## Run it yourself

```bash
pip install -r requirements.txt
python scripts/01_extract_transform.py --raw-dir raw --out-dir data   # download + tidy (~70 MB raw, not committed)
cd scripts
python 03_data_quality.py      # data quality gate: exits with an error if any FAIL check fails
python 02_build_marts.py       # build dashboard/data.js
python 03_data_quality.py      # re-run: also reconciles the report data to the warehouse (L03)
open ../dashboard/index.html   # or double-click it
```

To load into your own BigQuery project: replace the project ID in `sql/*.sql`, run `00` and `01`,
upload `data/fact_*.csv` (Create table → Upload, schema auto-detect), then run `02`, `03` and `04`.

## Data governance

Every number can be traced back to the source: SHA-256 fingerprints of the raw and output files, a row-level
reconciliation of every source row, control totals checked after loading, and an audit log of every quality run.
See **[DATA_GOVERNANCE.md](DATA_GOVERNANCE.md)** (ownership, lineage, the check framework, known source issues)
and **[DATA_DICTIONARY.md](DATA_DICTIONARY.md)** (tables, columns, allowed values, business definitions).

Current status: **20 passed, 2 warnings, 0 failed**. The warnings are a genuine inconsistency in Eurostat's
Serbia 2024 sector data and unusually fast (but plausible) growth in the Nordics and Lithuania.

## Notes on the data

- **Population:** enterprises with 10+ employees in industry and non-financial services (NACE C–N excl. K, plus 95.1).
- **Denominators differ by chart:** uses and sourcing are % of AI users; barriers are % of firms that *considered* AI but do not use it; everything else is % of all enterprises.
- **No AI survey in 2022.** Some questions (e.g. HR use, sourcing) are asked only in some waves, so they are missing for some years.
- Eurostat flags (u = low reliability, b = break in series) are carried through to the report.
- Source: Eurostat, *ICT usage and e-commerce in enterprises*, datasets `isoc_eb_ai` and `isoc_eb_ain2`, extract of 15 June 2026. © European Union. Reuse authorised under Commission Decision 2011/833/EU, provided the source is acknowledged. Independent analysis, not endorsed by Eurostat or the European Commission.
- **Privacy:** the data contains only country, sector and size-class percentages. No individual enterprise or person can be identified.

---
Part of [experiments](../README.md) by [Evangelos Papanastasis](https://evanpapanast.github.io/portfolio/).
