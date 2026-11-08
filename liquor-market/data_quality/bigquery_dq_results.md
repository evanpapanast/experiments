# BigQuery data quality checks (view `liquor_market.dq_results`)

Snapshot of 2026-11-08. **11 PASS, 0 WARN, 0 FAIL.** Rerun any time with
`SELECT * FROM liquor_market.dq_results ORDER BY check_id` (reads about 1.5 GB, inside the free tier).

| ID | Area | Rule | Result |
|---|---|---|---|
| R01 | Reconciliation | Monthly table matches the public source exactly (sales, litres, order lines) | ✅ PASS |
| R02 | Reconciliation | Every source category since 2017 is mapped to a product family | ✅ PASS |
| C01 | Completeness | Every month from the first to the last month is present | ✅ PASS |
| C02 | Completeness | All 11 product families are present | ✅ PASS |
| C03 | Completeness | Every family has a row in every month | ✅ PASS |
| V01 | Validity | Yearly gross margin is between 30% and 36% (fixed 50% markup by law) | ✅ PASS |
| V02 | Validity | No family has negative sales or litres in a month | ✅ PASS |
| V03 | Validity | Average price per litre is between $10 and $40 every year | ✅ PASS |
| K01 | Consistency | Price + volume + mix add up to the sales change | ✅ PASS |
| F01 | Forecast | Budget forecast: 11 families x 12 months x 2 measures, no gaps or errors | ✅ PASS |
| F02 | Forecast | Outlook forecast: 11 families x 20 months x 2 measures, no gaps or errors, value inside its range | ✅ PASS |
