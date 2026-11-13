-- Step 3a. Actuals by product family from the monthly table built in liquor-market/sql/02 (tiny scan).
-- Result saved as data/actuals_by_family.csv.
SELECT family,
  SUM(IF(month = '2026-04-01', sales_usd, 0)) AS sales_month,
  SUM(IF(month = '2026-04-01', liters, 0))    AS liters_month,
  SUM(IF(month = '2026-04-01', cost_usd, 0))  AS cost_month,
  SUM(IF(month = '2025-04-01', sales_usd, 0)) AS sales_same_month_last_year,
  SUM(IF(month = '2025-04-01', liters, 0))    AS liters_same_month_last_year,
  SUM(IF(month = '2026-03-01', sales_usd, 0)) AS sales_prior_month,
  SUM(IF(month BETWEEN '2026-01-01' AND '2026-04-01', sales_usd, 0)) AS sales_ytd,
  SUM(IF(month BETWEEN '2025-01-01' AND '2025-04-01', sales_usd, 0)) AS sales_ytd_last_year
FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly`
WHERE month >= '2025-01-01'
GROUP BY family ORDER BY family;
