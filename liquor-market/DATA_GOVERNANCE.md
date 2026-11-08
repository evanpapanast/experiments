# Data governance: Iowa spirits market

How the data is sourced, licensed, protected, checked and changed.

## 1. Source and licence

| Item | Value |
|---|---|
| Dataset | Iowa Liquor Sales (all spirits bought by Iowa Class E licensees, by product and date) |
| Publisher | Iowa Department of Revenue → Alcohol & Tax Operations Division → Alcohol Operations Bureau |
| Official page | https://data.iowa.gov/catalog/dataset/1051 (catalog record: https://catalog.data.gov/dataset/iowa-liquor-sales-2026) |
| Licence | **CC BY 4.0**: free to use, share and adapt, also commercially, if the source is credited, the licence is linked and changes are stated |
| Access level | Public |
| Read from | `bigquery-public-data.iowa_liquor_sales.sales` (Google BigQuery public datasets, a copy of the official data) |
| Licence checked | 8 November 2026 (2025 and 2026 yearly datasets and the 2012–current dataset all list CC BY 4.0) |

**How we meet the licence:** the report, the README and this document name the source, link the licence and state the
changes ("grouped into 11 product families and added up by month; forecasts, budgets and analysis are my own").
Check L01 fails if the credit or the licence link disappears from the report or the README.

## 2. Privacy and data minimisation

- The source contains **store names and addresses, supplier names and product names**. These are businesses, not private
  persons, but the report does not need them, so they are **never read into any output** (data minimisation).
- BigQuery keeps only `month × product family` totals (`fact_monthly`) and the category → family mapping.
- Checks P01–P03 fail if a store, supplier, product, address or place column, an unknown family name or long free text
  appears in a published file.
- No personal data is processed.

## 3. Lineage

```
bigquery-public-data.iowa_liquor_sales.sales
  → liquor_market.dim_category (11 families, 52 mapped category names)
  → liquor_market.fact_monthly (1,232 rows: 112 months × 11 families)
  → liquor_market.fc_budget_2026, fc_outlook, fc_total (AI.FORECAST)
  → liquor_market.m_* reporting views
  → sql/05_extract.sql → data/bigquery_extract.txt (SHA-256 in data/manifest.json)
  → scripts/01_build_report_data.py → data/*.csv, dashboard/data.js
```

**Control totals** (source, 2017-01-01 to 2026-04-30): sales $3,696,194,444 · litres 213,650,159 · order lines 23,308,845.
They are checked in BigQuery (R01, against the live source) and in GitHub (R02, against the manifest).

## 4. Quality checks

| Layer | Where | Checks | Result (8 Nov 2026) |
|---|---|---|---|
| Warehouse | BigQuery view `liquor_market.dq_results` | 11: reconciliation with the source, completeness, margin and price validity, bridge consistency, forecast completeness | 11 PASS |
| Published files | `scripts/02_data_quality.py`, GitHub Actions on every push and pull request | 22: privacy, licence credit, lineage fingerprint, control totals, completeness, validity, report consistency, accuracy and freshness | see [dq_report.md](data_quality/dq_report.md) |

**Severity:** FAIL stops publishing; WARN is reported for a person to review (forecast accuracy, freshness).

## 5. Key definitions (agreed business rules)

| Term | Rule |
|---|---|
| Sales | What stores paid the state (state bottle retail × bottles), net of credits |
| Cost and gross margin | Cost = what the state paid suppliers; margin = sales − cost (about one third, because of the fixed 50% markup) |
| Price | Sales per litre |
| Volume / mix / price effects | Volume = change in litres × last period's average price; mix = effect of the family mix; price = change in price per litre within each family. They always add up to the sales change (K01/K02) |
| Budget | AI.FORECAST made with data up to December of the last full year, by family, for sales and litres |
| Budget gap split | Volume part = (actual − budget litres) × budget price; price part = (actual − budget price) × actual litres |
| Family status | Holding steady: sales change ≥ −1%. Price hides falling volume: litres ≤ −3% and price ≥ +2%. Losing ground: all others |

## 6. Change control

- All changes go through a pull request; the GitHub Actions quality gate must pass before merging.
- The category → family mapping (`sql/01_dim_category.sql`) is reviewed by hand; check R02 in BigQuery warns if the
  source adds a category that is not mapped.
- **Refresh:** rerun `sql/02`–`sql/06`, then `sql/05`, update the extract and manifest (control totals, fingerprint),
  then `scripts/01` and `scripts/02`.

## 7. Cost and access

- BigQuery dataset `liquor_market` (location US) is private to the project owner; only aggregates are published.
- All work fits in the free tier (largest query about 2 GB of the 1 TB free each month; forecasts read under 0.1 MB).
