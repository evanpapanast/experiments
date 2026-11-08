# Data dictionary: Iowa spirits market

Amounts are US dollars, volumes are litres. "Family" is one of 11 product families. No file contains store, supplier or product names.

## BigQuery (`liquor_market` dataset)

| Object | Type | Grain | Columns |
|---|---|---|---|
| `dim_category` | table | source category | `category_name`, `family` |
| `fact_monthly` | table | month × family (1,232 rows) | `month`, `family`, `order_lines`, `credit_lines` (lines with negative sales), `sales_usd`, `cost_usd`, `liters`, `bottles` |
| `fc_budget_2026` | table | measure × family × month | `measure` (sales_usd / liters), `family`, `month`, `forecast_value`, `lower_80`, `upper_80`, `ai_forecast_status`: forecast made with data to Dec 2025 |
| `fc_outlook` | table | measure × family × month | as above, made with all data, to Dec 2027 |
| `fc_total` | table | version × month | whole-market forecast with its 80% range (`outlook`, `budget_2026`) |
| `m_year_family` | view | year × family | sales, cost, litres, bottles, price per litre, `is_ytd` |
| `m_month_total` | view | month | sales, cost, litres |
| `m_pvm` / `m_pvm_family` | view | comparison (× family) | sales and litres before/after; volume, mix and price effects |
| `m_budget_vs_actual` | view | family × month | budget and actual sales and litres |
| `m_outlook_family` | view | family × year | sales and litres: actual 2025, actual + forecast 2026, forecast 2027 |
| `m_seasonality` | view | calendar month | average, lowest and highest share of the year's sales (2017–2025) |
| `dq_results` | view | check | `check_id`, `category`, `severity`, `rule`, `failures`, `status`, `checked_at` |

## Published files (`data/`)

| File | Grain | Columns |
|---|---|---|
| `bigquery_extract.txt` | – | all blocks below in one text file, as copied from BigQuery (fingerprinted in the manifest) |
| `year_family.csv` | year × family | `year`, `family`, `sales_usd`, `cost_usd`, `liters` |
| `month_total.csv` | month | `month`, `sales_usd`, `cost_usd`, `liters` |
| `seasonality.csv` | calendar month | `month_of_year`, `avg_share`, `min_share`, `max_share` |
| `pvm_family.csv` | comparison × family | `comparison`, `family`, `sales_before`, `sales_after`, `liters_before`, `liters_after` |
| `budget_vs_actual_month.csv` | month | `month`, `budget_sales`, `budget_liters`, `actual_sales`, `actual_liters` |
| `budget_vs_actual_family.csv` | family | same, for the months with actuals |
| `budget_2026_family.csv` | family | full-year budget: `budget_sales`, `budget_liters` |
| `outlook_family.csv` | family × year | `sales_usd`, `liters` |
| `outlook_month_sum.csv` | measure × month | family forecasts added up: `forecast`, `lower_80_sum`, `upper_80_sum` |
| `forecast_total.csv` | version × month | whole-market forecast, rounded to $10,000: `forecast`, `lower_80`, `upper_80` |
| `manifest.json` | – | source, licence, BigQuery objects, control totals, extract fingerprint, quality snapshot |

## Report (`dashboard/`)

`data.js` (`window.LIQ`) holds every number and sentence the report shows, built by `scripts/01_build_report_data.py`.
The forecast range on the monthly chart uses the whole-market model's 80% range, applied to the family forecasts added up.
