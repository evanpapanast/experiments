-- Step 4. Forecast check: what would the model have said for April using data only up to March?
-- Result saved as data/forecast_check.csv.
SELECT DATE(forecast_timestamp) AS month, ROUND(forecast_value) AS forecast,
       ROUND(prediction_interval_lower_bound) AS low_80, ROUND(prediction_interval_upper_bound) AS high_80
FROM AI.FORECAST(
  (SELECT TIMESTAMP(month) AS month, SUM(sales_usd) AS sales
   FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly` WHERE month <= '2026-03-01' GROUP BY month),
  data_col => 'sales', timestamp_col => 'month', horizon => 1, confidence_level => 0.8);

-- Step 5. Re-forecast May to December with data up to April. Result saved as data/reforecast.csv.
SELECT DATE(forecast_timestamp) AS month, ROUND(forecast_value) AS forecast,
       ROUND(prediction_interval_lower_bound) AS low_80, ROUND(prediction_interval_upper_bound) AS high_80
FROM AI.FORECAST(
  (SELECT TIMESTAMP(month) AS month, SUM(sales_usd) AS sales
   FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly` WHERE month <= '2026-04-01' GROUP BY month),
  data_col => 'sales', timestamp_col => 'month', horizon => 8, confidence_level => 0.8)
ORDER BY month;
