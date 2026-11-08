-- Forecasts with BigQuery's built-in TimesFM model (AI.FORECAST), one series per product family.
-- 1) "Budget 2026": made as if in December 2025, using only data up to December 2025 (12 months ahead).
-- 2) "Outlook": made with all data up to the latest month (to December 2027).
-- Sales (USD) and volume (litres) are forecast separately, so budgets can be split into price and volume.

CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.liquor_market.fc_budget_2026` AS
SELECT 'sales_usd' AS measure, family, DATE(forecast_timestamp) AS month, forecast_value,
       prediction_interval_lower_bound AS lower_80, prediction_interval_upper_bound AS upper_80, ai_forecast_status
FROM AI.FORECAST(
  (SELECT TIMESTAMP(month) AS ts, family, sales_usd FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly`
   WHERE month <= '2025-12-01'),
  data_col => 'sales_usd', timestamp_col => 'ts', id_cols => ['family'], horizon => 12, confidence_level => 0.8)
UNION ALL
SELECT 'liters', family, DATE(forecast_timestamp), forecast_value,
       prediction_interval_lower_bound, prediction_interval_upper_bound, ai_forecast_status
FROM AI.FORECAST(
  (SELECT TIMESTAMP(month) AS ts, family, liters FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly`
   WHERE month <= '2025-12-01'),
  data_col => 'liters', timestamp_col => 'ts', id_cols => ['family'], horizon => 12, confidence_level => 0.8);

CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.liquor_market.fc_outlook` AS
SELECT 'sales_usd' AS measure, family, DATE(forecast_timestamp) AS month, forecast_value,
       prediction_interval_lower_bound AS lower_80, prediction_interval_upper_bound AS upper_80, ai_forecast_status
FROM AI.FORECAST(
  (SELECT TIMESTAMP(month) AS ts, family, sales_usd FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly`),
  data_col => 'sales_usd', timestamp_col => 'ts', id_cols => ['family'], horizon => 20, confidence_level => 0.8)
UNION ALL
SELECT 'liters', family, DATE(forecast_timestamp), forecast_value,
       prediction_interval_lower_bound, prediction_interval_upper_bound, ai_forecast_status
FROM AI.FORECAST(
  (SELECT TIMESTAMP(month) AS ts, family, liters FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly`),
  data_col => 'liters', timestamp_col => 'ts', id_cols => ['family'], horizon => 20, confidence_level => 0.8);

-- Total market (all families together), for the headline chart with its uncertainty band.
CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.liquor_market.fc_total` AS
SELECT 'outlook' AS version, DATE(forecast_timestamp) AS month, forecast_value,
       prediction_interval_lower_bound AS lower_80, prediction_interval_upper_bound AS upper_80
FROM AI.FORECAST(
  (SELECT TIMESTAMP(month) AS ts, SUM(sales_usd) AS sales_usd
   FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly` GROUP BY ts),
  data_col => 'sales_usd', timestamp_col => 'ts', horizon => 20, confidence_level => 0.8)
UNION ALL
SELECT 'budget_2026', DATE(forecast_timestamp), forecast_value,
       prediction_interval_lower_bound, prediction_interval_upper_bound
FROM AI.FORECAST(
  (SELECT TIMESTAMP(month) AS ts, SUM(sales_usd) AS sales_usd
   FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly` WHERE month <= '2025-12-01' GROUP BY ts),
  data_col => 'sales_usd', timestamp_col => 'ts', horizon => 12, confidence_level => 0.8);
