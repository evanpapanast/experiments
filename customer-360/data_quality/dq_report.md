# Data quality report: Customer 360

Run on the published files. 26 of 26 checks passed.

| Area | Check | Result | Detail |
|---|---|---|---|
| Traceability | Extract fingerprint matches manifest (SHA-256) | PASS | 2885481837d7b9e5… |
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
| Governance | All dbt tests in BigQuery passed | PASS | 43 of 43 |
| Governance | Report data was generated from the extract | PASS | header present |
| Governance | Report states that the data is synthetic | PASS | banner present |
| Governance | Report loads no external scripts or trackers | PASS | local scripts only |
| Governance | Marketing spend is not invented | PASS | no spend-based metrics in report data |

## dbt tests in BigQuery (dbt/, 43 tests)

| Area | Check | Result | Status |
|---|---|---|---|
| Privacy | assert_adults_only | 0 failing rows | PASS |
| Privacy | assert_no_personal_data_columns | 0 failing rows | PASS |
| Privacy | min_group_size_rpt_channel_acquisition_registered | 0 failing rows | PASS |
| Privacy | min_group_size_rpt_channel_purchase_customers | 0 failing rows | PASS |
| Privacy | min_group_size_rpt_demographics_customers | 0 failing rows | PASS |
| Privacy | min_group_size_rpt_region_channel_customers | 0 failing rows | PASS |
| Privacy | min_group_size_rpt_segment_channel_customers | 0 failing rows | PASS |
| Privacy | min_group_size_rpt_segments_customers | 0 failing rows | PASS |
| Accuracy | assert_order_lines_reconcile_to_source | 0 failing rows | PASS |
| Accuracy | assert_segments_equal_channels | 0 failing rows | PASS |
| Completeness | assert_every_customer_in_one_group | 0 failing rows | PASS |
| Completeness | not_null_int_customer_metrics_customer_id | 0 failing rows | PASS |
| Completeness | not_null_int_customer_metrics_segment | 0 failing rows | PASS |
| Completeness | not_null_rpt_channel_acquisition_channel | 0 failing rows | PASS |
| Completeness | not_null_rpt_channel_purchase_channel | 0 failing rows | PASS |
| Completeness | not_null_rpt_funnel_channel | 0 failing rows | PASS |
| Completeness | not_null_rpt_segments_segment | 0 failing rows | PASS |
| Completeness | not_null_stg_customers_acquisition_channel | 0 failing rows | PASS |
| Completeness | not_null_stg_customers_customer_id | 0 failing rows | PASS |
| Completeness | not_null_stg_order_items_customer_id | 0 failing rows | PASS |
| Completeness | not_null_stg_order_items_order_item_id | 0 failing rows | PASS |
| Completeness | not_null_stg_sessions_session_id | 0 failing rows | PASS |
| Reproducibility | assert_preferred_channel_is_deterministic | 0 failing rows | PASS |
| Integrity | assert_all_orders_attributed | 0 failing rows | PASS |
| Integrity | relationships_stg_order_items_customer_id | 0 failing rows | PASS |
| Uniqueness | unique_int_customer_metrics_customer_id | 0 failing rows | PASS |
| Uniqueness | unique_rpt_channel_acquisition_channel | 0 failing rows | PASS |
| Uniqueness | unique_rpt_channel_purchase_channel | 0 failing rows | PASS |
| Uniqueness | unique_rpt_funnel_channel | 0 failing rows | PASS |
| Uniqueness | unique_rpt_segments_segment | 0 failing rows | PASS |
| Uniqueness | unique_stg_customers_customer_id | 0 failing rows | PASS |
| Uniqueness | unique_stg_order_items_order_item_id | 0 failing rows | PASS |
| Uniqueness | unique_stg_sessions_session_id | 0 failing rows | PASS |
| Validity | accepted_values_int_customer_metrics_preferred_channel | 0 failing rows | PASS |
| Validity | accepted_values_int_customer_metrics_segment | 0 failing rows | PASS |
| Validity | accepted_values_stg_customers_age_band | 0 failing rows | PASS |
| Validity | accepted_values_stg_customers_gender | 0 failing rows | PASS |
| Validity | accepted_values_stg_customers_region | 0 failing rows | PASS |
| Validity | accepted_values_stg_order_items_status | 0 failing rows | PASS |
| Validity | accepted_values_stg_sessions_channel | 0 failing rows | PASS |
| Validity | assert_dates_in_window | 0 failing rows | PASS |
| Validity | between_stg_order_items_product_cost | 0 failing rows | PASS |
| Validity | between_stg_order_items_sale_price | 0 failing rows | PASS |
