# Data quality report: Iowa spirits market

Checks on the published files. **22 PASS, 0 WARN, 0 FAIL.** The warehouse checks in BigQuery are in [bigquery_dq_results.md](bigquery_dq_results.md).

| ID | Area | Rule | Result | Problems | Detail |
|---|---|---|---|---|---|
| P01 | Privacy | Published data files contain only approved columns (no store, supplier, product or place) | ✅ PASS | 0 |  |
| P02 | Privacy | Only the 11 approved product families appear (no brand or company names) | ✅ PASS | 0 |  |
| P03 | Privacy | No free-text cell longer than 40 characters in the data files | ✅ PASS | 0 |  |
| L01 | Licence | Licence is CC BY 4.0 and the report and README credit the source and link the licence | ✅ PASS | 0 |  |
| R01 | Lineage | The extract file is the one recorded in the manifest (SHA-256) | ✅ PASS | 0 |  |
| R02 | Reconciliation | Yearly and monthly totals match the source control totals (within $5 / 5 litres of rounding) | ✅ PASS | 0 | largest difference 3 |
| R03 | Reconciliation | Price/volume inputs agree with the yearly totals | ✅ PASS | 0 |  |
| R04 | Reconciliation | Budget vs actual agrees by month, by family and with the yearly totals | ✅ PASS | 0 |  |
| R05 | Reconciliation | The outlook starts from the real 2025 sales | ✅ PASS | 0 |  |
| C01 | Completeness | Every month from January 2017 to the latest month is present | ✅ PASS | 0 |  |
| C02 | Completeness | All 11 families are present in every year | ✅ PASS | 0 |  |
| C03 | Completeness | Seasonality covers 12 months and its shares add up to 100% | ✅ PASS | 0 |  |
| C04 | Completeness | The forecast covers every month from the next month to December of next year | ✅ PASS | 0 |  |
| V01 | Validity | Yearly gross margin is between 30% and 36% (fixed 50% markup by law) | ✅ PASS | 0 | range 33.1% to 33.4% |
| V02 | Validity | No negative sales, litres or forecasts | ✅ PASS | 0 |  |
| V03 | Validity | Every forecast lies inside its likely range | ✅ PASS | 0 |  |
| K01 | Consistency | Headline numbers in the report equal the data files | ✅ PASS | 0 |  |
| K02 | Consistency | Price + volume + mix add up to the sales change in the report | ✅ PASS | 0 |  |
| K03 | Consistency | Budget gap = volume part + price part, for every family | ✅ PASS | 0 |  |
| K04 | Consistency | The report data was built from the current extract (same last month) | ✅ PASS | 0 |  |
| A01 | Accuracy | Forecast-based budget within 5% of actual sales so far this year | ✅ PASS | 0 | 3.0% off |
| F01 | Freshness | Latest month is no more than 8 months old (the source publishes with a delay) | ✅ PASS | 0 | latest month 2026-04, 7 months ago |
