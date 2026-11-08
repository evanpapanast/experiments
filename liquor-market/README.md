# Iowa spirits market: where sales are going and what to do

**[Open the interactive report →](https://evanpapanast.github.io/experiments/liquor-market/dashboard/)**

A management report built the way a finance team would: **business question → free, legal data → actionable insights.**
Built in Google BigQuery, with BigQuery's built-in forecasting.

## The business questions

For a company selling spirits in Iowa:

1. Are sales growing because people buy more, or only because prices rise?
2. How good was the budget?
3. What should we plan for next year, and where should we act?

## What we found

| | |
|---|---|
| **Volume, not price** | 2025 sales fell 5.0% to $425.0m. Fewer litres cost $21.5m; price added only $1.0m. Litres sold are 10% below their 2021 peak. |
| **Below budget** | A forecast-based budget made in December 2025 expected growth. January–April 2026 came in 3.0% below it, almost all because of lower volume. |
| **Plan on a range** | 2027: $393m if the current trend continues, up to $432m if the forecast model is right. The model was too optimistic this year, so the low end is the base case. |
| **Act by family** | Holding steady: American whiskey, rum. Price hides falling volume: liqueurs, Canadian whisky, gin, ready-to-drink cocktails, gift packs. Losing ground: vodka, tequila, brandy, Scotch & Irish whisky. |
| **Calendar** | October and December bring 19% of the year's sales; January is the weakest month. Split the budget by month accordingly. |

## How it works

```
BigQuery public data (34 million order lines)
   └─► sql/01  group 44 categories into 11 product families
   └─► sql/02  monthly table, checked against the source (exact match)
   └─► sql/03  forecasts with AI.FORECAST (budget as of Dec 2025, outlook to Dec 2027)
   └─► sql/04  reporting views: price/volume/mix, budget vs actual, outlook, seasonality
   └─► sql/06  11 quality checks inside BigQuery
   └─► sql/05  compact extract ──► scripts/01  report data and plain-language insights ──► dashboard/
                                  scripts/02  22 checks on the published files (GitHub Actions)
```

| Step | File |
|---|---|
| Product families (hand-reviewed mapping) | `sql/01_dim_category.sql` |
| Monthly table from the public data | `sql/02_fact_monthly.sql` |
| Forecasts (TimesFM, built into BigQuery) | `sql/03_forecasts.sql` |
| Reporting views | `sql/04_marts.sql` |
| Extract for the report | `sql/05_extract.sql` → `data/bigquery_extract.txt` |
| Quality checks in BigQuery | `sql/06_data_quality_checks.sql` → `data_quality/bigquery_dq_results.md` |
| Report data, insights and actions | `scripts/01_build_report_data.py` → `dashboard/data.js` |
| Quality gate on published files | `scripts/02_data_quality.py` → `data_quality/dq_report.md` |

## Quality and governance

- **Reconciled:** the monthly table matches the public source exactly: $3,696,194,444 of sales, 213,650,159 litres and 23,308,845 order lines (January 2017 to April 2026).
- **Checked twice:** 11 checks in BigQuery and 22 checks on the published files; the second set runs automatically on every change.
- **Traceable:** every SQL statement that ran is in `sql/`; the extract is fingerprinted (SHA-256) in `data/manifest.json`.
- See [DATA_GOVERNANCE.md](DATA_GOVERNANCE.md) and [DATA_DICTIONARY.md](DATA_DICTIONARY.md).

## Data, licence and privacy

- **Source:** Iowa Department of Revenue, Alcohol Operations Bureau, *Iowa Liquor Sales*, licensed under
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (free to use and share with credit). Read from the Google BigQuery public datasets.
- **Changes made:** grouped into 11 product families and added up by month; forecasts, budgets and analysis are my own.
- **No names:** the source lists stores, suppliers and products. None of these are kept: the report uses totals by product family and month only.
- **Cost:** inside BigQuery's free tier.

This is an analysis of public data, not investment or business advice.

---
Part of [experiments](../README.md) by [Evangelos Papanastasis](https://evanpapanast.github.io/portfolio/).
