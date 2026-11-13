-- Step 3b. Budget by product family: the forecast-based 2026 budget made in December 2025 (liquor-market/sql/03).
-- Result saved as data/budget_by_family.csv.
SELECT family,
  SUM(IF(measure = 'sales_usd' AND month = '2026-04-01', forecast_value, 0)) AS budget_sales_month,
  SUM(IF(measure = 'liters'    AND month = '2026-04-01', forecast_value, 0)) AS budget_liters_month,
  SUM(IF(measure = 'sales_usd' AND month <= '2026-04-01', forecast_value, 0)) AS budget_sales_ytd,
  SUM(IF(measure = 'sales_usd', forecast_value, 0)) AS budget_sales_full_year,
  SUM(IF(measure = 'sales_usd' AND month > '2026-04-01', forecast_value, 0)) AS budget_sales_rest_of_year
FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fc_budget_2026`
GROUP BY family ORDER BY family;
