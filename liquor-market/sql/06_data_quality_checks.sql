-- Data quality checks inside BigQuery. One row per check: FAIL checks must be 0 before the report is published.
-- R01 reads the public source table (about 1 GB per run; within the free tier).
CREATE OR REPLACE VIEW `project-57338774-2b06-4ac1-ba9.liquor_market.dq_results` AS
WITH
src AS (
  SELECT ROUND(SUM(sale_dollars), 0) AS s, ROUND(SUM(volume_sold_liters), 0) AS l, COUNT(*) AS n
  FROM `bigquery-public-data.iowa_liquor_sales.sales`
  WHERE date >= '2017-01-01'
    AND date < DATE_ADD((SELECT MAX(month) FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly`), INTERVAL 1 MONTH)
),
fct AS (
  SELECT ROUND(SUM(sales_usd), 0) AS s, ROUND(SUM(liters), 0) AS l, SUM(order_lines) AS n,
         COUNT(DISTINCT month) AS months, MIN(month) AS first_m, MAX(month) AS last_m, COUNT(DISTINCT family) AS fams, COUNT(*) AS rows_
  FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly`
),
unmapped AS (
  SELECT COUNT(DISTINCT s.category_name) AS n
  FROM `bigquery-public-data.iowa_liquor_sales.sales` s
  LEFT JOIN `project-57338774-2b06-4ac1-ba9.liquor_market.dim_category` c USING (category_name)
  WHERE s.date >= '2017-01-01' AND s.category_name IS NOT NULL AND c.family IS NULL
),
yr AS (
  SELECT EXTRACT(YEAR FROM month) AS y, 1 - SUM(cost_usd) / SUM(sales_usd) AS margin, SUM(sales_usd) / SUM(liters) AS price
  FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly` GROUP BY y
),
pvm AS (SELECT COUNTIF(ABS(volume_effect + mix_effect + price_effect - (sales_after - sales_before)) > 1) AS bad
        FROM `project-57338774-2b06-4ac1-ba9.liquor_market.m_pvm`),
fb AS (SELECT COUNT(*) AS n, COUNTIF(forecast_value IS NULL) AS n_null, COUNTIF(ai_forecast_status != '') AS errs
       FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fc_budget_2026`),
fo AS (SELECT COUNT(*) AS n, COUNTIF(forecast_value IS NULL) AS n_null, COUNTIF(ai_forecast_status != '') AS errs,
              COUNTIF(lower_80 > forecast_value OR upper_80 < forecast_value) AS band_bad
       FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fc_outlook`),
checks AS (
  SELECT 'R01' AS check_id, 'Reconciliation' AS category, 'FAIL' AS severity,
         'Monthly table matches the public source exactly (sales, litres, order lines)' AS rule,
         (SELECT IF(src.s = fct.s, 0, 1) + IF(src.l = fct.l, 0, 1) + IF(src.n = fct.n, 0, 1) FROM src, fct) AS failures
  UNION ALL SELECT 'R02', 'Reconciliation', 'WARN', 'Every source category since 2017 is mapped to a product family',
         (SELECT n FROM unmapped)
  UNION ALL SELECT 'C01', 'Completeness', 'FAIL', 'Every month from the first to the last month is present',
         (SELECT DATE_DIFF(last_m, first_m, MONTH) + 1 - months FROM fct)
  UNION ALL SELECT 'C02', 'Completeness', 'FAIL', 'All 11 product families are present',
         (SELECT ABS(fams - 11) FROM fct)
  UNION ALL SELECT 'C03', 'Completeness', 'WARN', 'Every family has a row in every month',
         (SELECT months * fams - rows_ FROM fct)
  UNION ALL SELECT 'V01', 'Validity', 'FAIL', 'Yearly gross margin is between 30% and 36% (fixed 50% markup by law)',
         (SELECT COUNTIF(margin NOT BETWEEN 0.30 AND 0.36) FROM yr)
  UNION ALL SELECT 'V02', 'Validity', 'FAIL', 'No family has negative sales or litres in a month',
         (SELECT COUNTIF(sales_usd < 0 OR liters < 0) FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly`)
  UNION ALL SELECT 'V03', 'Validity', 'WARN', 'Average price per litre is between $10 and $40 every year',
         (SELECT COUNTIF(price NOT BETWEEN 10 AND 40) FROM yr)
  UNION ALL SELECT 'K01', 'Consistency', 'FAIL', 'Price + volume + mix add up to the sales change',
         (SELECT bad FROM pvm)
  UNION ALL SELECT 'F01', 'Forecast', 'FAIL', 'Budget forecast: 11 families x 12 months x 2 measures, no gaps or errors',
         (SELECT ABS(n - 264) + n_null + errs FROM fb)
  UNION ALL SELECT 'F02', 'Forecast', 'FAIL', 'Outlook forecast: 11 families x 20 months x 2 measures, no gaps or errors, value inside its range',
         (SELECT ABS(n - 440) + n_null + errs + band_bad FROM fo)
)
SELECT check_id, category, severity, rule, failures, IF(failures = 0, 'PASS', severity) AS status,
       CURRENT_TIMESTAMP() AS checked_at
FROM checks;
