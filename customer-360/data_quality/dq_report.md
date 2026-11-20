# Data quality report: Customer 360

Run on the published files. 26 of 26 checks passed.

| Area | Check | Result | Detail |
|---|---|---|---|
| Traceability | Extract fingerprint matches manifest (SHA-256) | PASS | 2f564543368ef8a5… |
| Traceability | Every data file is listed in the manifest | PASS | 8 files |
| Privacy | Only approved columns are published | PASS | all columns approved |
| Privacy | No personal-data or row-level ID columns | PASS | none |
| Privacy | Every published group has at least 50 customers | PASS | 0 small groups |
| Privacy | Small cells are suppressed, not dropped | PASS | 2 suppressed cells (expected 2) |
| Privacy | Extract holds no e-mail addresses or IP addresses | PASS | pattern scan |
| Accuracy | Net revenue: groups = channels | PASS | 4,378,159 vs 4,378,161 |
| Accuracy | Net revenue: groups = categories | PASS | 4,378,158 vs 4,378,161 |
| Accuracy | Net revenue: groups = first channels | PASS | 4,378,160 vs 4,378,161 |
| Accuracy | Net revenue: groups = months | PASS | 4,378,161 vs 4,378,161 |
| Accuracy | Gross margin: groups = channels | PASS | 2,274,643 vs 2,274,643 |
| Completeness | Customers by region add up to all customers | PASS | 89,819 vs 89,819 |
| Completeness | Customers by age_band add up to all customers | PASS | 89,819 vs 89,819 |
| Completeness | Customers by gender add up to all customers | PASS | 89,819 vs 89,819 |
| Completeness | Buyers by region and preferred channel add up to all buyers | PASS | 43,411 vs 43,411 |
| Completeness | All five channels present | PASS | Email, Facebook, Google Ads, Organic, YouTube |
| Validity | Rates and shares are between 0 and 1 | PASS | 25 values |
| Validity | Revenue shares add up to 100% | PASS | 1.0000 |
| Validity | No negative values | PASS | 0 negative values |
| Validity | Months cover the 24-month window | PASS | 2024-11 to 2026-11 (25 months, first and last partial) |
| Governance | All BigQuery checks passed | PASS | 15 of 15 |
| Governance | Report data was generated from the extract | PASS | header present |
| Governance | Report states that the data is synthetic | PASS | banner present |
| Governance | Report loads no external scripts or trackers | PASS | local scripts only |
| Governance | Marketing spend is not invented | PASS | no spend-based metrics in report data |

## Checks inside BigQuery (sql/04_quality_checks.sql)

| Area | Check | Result | Status |
|---|---|---|---|
| Privacy | No personal-data columns (names, email, address, postcode, city, IP, browser, exact age, GPS, country) | 0 | PASS |
| Privacy | Only adults (18+) included: customer count matches source adults | 89819 vs 89819 | PASS |
| Privacy | Every published group has 50+ customers (smaller cells suppressed) | 0 | PASS |
| Completeness | Order lines reconcile to source | 97855 vs 97855 | PASS |
| Accuracy | Net revenue reconciles to source | 4378159 vs 4378159 | PASS |
| Accuracy | Segment revenue = channel revenue (two views agree) | 4378161 vs 4378159 | PASS |
| Completeness | Every customer is in exactly one segment | 89819 vs 89819 | PASS |
| Uniqueness | No duplicate order lines | 0 | PASS |
| Uniqueness | No duplicate customers | 0 | PASS |
| Uniqueness | No duplicate sessions | 0 | PASS |
| Validity | Order dates inside 20 Nov 2024 - 19 Nov 2026 | 2024-11-20 to 2026-11-19 | PASS |
| Validity | Session dates inside window | 2024-11-20 to 2026-11-19 | PASS |
| Validity | Prices and product costs are positive | 0 | PASS |
| Integrity | Every order line links to a known customer | 0 | PASS |
| Integrity | Orders linked to a purchase visit (channel known) | 0 unattributed lines | PASS |
