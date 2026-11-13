# Run log: 2026-04 close

Every BigQuery query that ran for this close, in order. SQL is in `sql/`, results are saved unchanged in `data/`.

| Step | Purpose | SQL | Result file | GB billed | Rows | Date |
|---|---|---|---|---|---|---|
| 0 | Size check before running (dry run) | 01_new_data_check.sql | – | 0.00 | 0 | 2026-11-13 |
| 1 | New data check | 01_new_data_check.sql | source_months.csv | 0.82 | 2 | 2026-11-13 |
| 0 | Size check before running (dry run) | 02_source_quality_checks.sql | – | 0.00 | 0 | 2026-11-13 |
| 2 | Source quality checks | 02_source_quality_checks.sql | source_checks.csv | 2.84 | 2 | 2026-11-13 |
| 2 | Follow-up on price per litre warning | 02_source_quality_checks.sql | price_outliers.csv | 1.09 | 2 | 2026-11-13 |
| 3 | Actuals by family | 03_actuals_by_family.sql | actuals_by_family.csv | 0.02 | 11 | 2026-11-13 |
| 3 | Budget by family | 04_budget_by_family.sql | budget_by_family.csv | 0.01 | 11 | 2026-11-13 |
| 4 | Forecast check (data to March) | 05_forecasts.sql | forecast_check.csv | 0.01 | 1 | 2026-11-13 |
| 5 | Re-forecast May-Dec (data to April) | 05_forecasts.sql | reforecast.csv | 0.01 | 8 | 2026-11-13 |
| - | Exploration: table columns and budget table preview (not used in results) | – | – | 0.02 | 15 | 2026-11-13 |

**Total: 4.82 GB billed**, inside BigQuery's free 1 TB a month. All queries were read-only: nothing in BigQuery was created or changed.

## Input fingerprints (SHA-256)

If any input file is edited after the run, its fingerprint will no longer match.

| File | SHA-256 |
|---|---|
| actuals_by_family.csv | `6d498f3632b4548f60eee216eddf455a3ed6c5a83549c28b70e5a23c26bbaaf3` |
| budget_by_family.csv | `8ffcc3fc3da1f38343f6965ea74932aa855ba45bf75e7c3d37566bda4e1a6150` |
| forecast_check.csv | `6914c5ac20cb71264065694f1f91a25ff06ca49e71b4266768ae8d140376f7a9` |
| price_outliers.csv | `502276633d5fd9493152df621fea8d74629387af474c1490c6c69203a5fad21b` |
| query_log.csv | `8c14f9a910520ace5016a8d2b4026c0294772123c57ce489fb91bad44e38d97d` |
| reforecast.csv | `52f5ef414615c778e07d71ee790c71a3d6109c5ed79f402b49ce6f81655ef215` |
| source_checks.csv | `00f52c7278c25585a4c90d09296340b809055196837463798c992509f54a4a82` |
| source_months.csv | `16c3422aa8d62ad8098acae1cd98f63a50495d9e24939662fbecddc92cf643ed` |

## Outcome

- Checks: 17 pass or info, 2 warnings, 0 failures (see `checks.md`).
- Report data: written to `dashboard/data.js`.
- Publishing: by pull request only; a person reviews and merges.
