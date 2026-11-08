-- Reporting views. Price = sales per litre. Periods: full years 2017-2025, 2026 year to date (YTD).

-- 1. Year by product family
CREATE OR REPLACE VIEW `project-57338774-2b06-4ac1-ba9.liquor_market.m_year_family` AS
WITH last_m AS (SELECT MAX(month) AS m FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly`)
SELECT EXTRACT(YEAR FROM f.month) AS year, f.family,
       EXTRACT(YEAR FROM f.month) = EXTRACT(YEAR FROM l.m) AS is_ytd,
       SUM(f.sales_usd) AS sales_usd, SUM(f.cost_usd) AS cost_usd, SUM(f.liters) AS liters, SUM(f.bottles) AS bottles,
       SAFE_DIVIDE(SUM(f.sales_usd), SUM(f.liters)) AS price_per_liter
FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly` f CROSS JOIN last_m l
GROUP BY year, f.family, is_ytd;

-- 2. Month, whole market
CREATE OR REPLACE VIEW `project-57338774-2b06-4ac1-ba9.liquor_market.m_month_total` AS
SELECT month, SUM(sales_usd) AS sales_usd, SUM(cost_usd) AS cost_usd, SUM(liters) AS liters
FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly`
GROUP BY month;

-- 3. Price / volume / mix bridge for two comparisons:
--    full year 2025 vs 2024, and 2026 year to date vs the same months of 2025.
--    volume = change in litres at last period's average price
--    mix    = effect of selling more of the dearer or cheaper families
--    price  = change in price per litre within each family
CREATE OR REPLACE VIEW `project-57338774-2b06-4ac1-ba9.liquor_market.m_pvm` AS
WITH last_m AS (SELECT MAX(month) AS m FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly`),
periods AS (
  SELECT 'FY2025 vs FY2024' AS comparison, DATE '2024-01-01' AS b0, DATE '2024-12-01' AS e0,
         DATE '2025-01-01' AS b1, DATE '2025-12-01' AS e1 FROM last_m
  UNION ALL
  SELECT 'YTD2026 vs YTD2025', DATE '2025-01-01', DATE_SUB(m, INTERVAL 12 MONTH), DATE '2026-01-01', m FROM last_m
),
fam AS (
  SELECT p.comparison, f.family,
         SUM(IF(f.month BETWEEN p.b0 AND p.e0, f.sales_usd, 0)) AS s0, SUM(IF(f.month BETWEEN p.b0 AND p.e0, f.liters, 0)) AS l0,
         SUM(IF(f.month BETWEEN p.b1 AND p.e1, f.sales_usd, 0)) AS s1, SUM(IF(f.month BETWEEN p.b1 AND p.e1, f.liters, 0)) AS l1
  FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly` f CROSS JOIN periods p
  GROUP BY p.comparison, f.family
),
tot AS (SELECT comparison, SUM(s0) s0, SUM(l0) l0, SUM(s1) s1, SUM(l1) l1,
               SUM(l1 * SAFE_DIVIDE(s0, l0)) AS s1_at_p0 FROM fam GROUP BY comparison)
SELECT comparison, s0 AS sales_before, s1 AS sales_after, l0 AS liters_before, l1 AS liters_after,
       (l1 - l0) * (s0 / l0)          AS volume_effect,
       s1_at_p0 - l1 * (s0 / l0)      AS mix_effect,
       s1 - s1_at_p0                  AS price_effect
FROM tot;

-- 4. Price and volume change by family, same two comparisons
CREATE OR REPLACE VIEW `project-57338774-2b06-4ac1-ba9.liquor_market.m_pvm_family` AS
WITH last_m AS (SELECT MAX(month) AS m FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly`),
periods AS (
  SELECT 'FY2025 vs FY2024' AS comparison, DATE '2024-01-01' AS b0, DATE '2024-12-01' AS e0,
         DATE '2025-01-01' AS b1, DATE '2025-12-01' AS e1 FROM last_m
  UNION ALL
  SELECT 'YTD2026 vs YTD2025', DATE '2025-01-01', DATE_SUB(m, INTERVAL 12 MONTH), DATE '2026-01-01', m FROM last_m
)
SELECT p.comparison, f.family,
       SUM(IF(f.month BETWEEN p.b0 AND p.e0, f.sales_usd, 0)) AS sales_before,
       SUM(IF(f.month BETWEEN p.b1 AND p.e1, f.sales_usd, 0)) AS sales_after,
       SUM(IF(f.month BETWEEN p.b0 AND p.e0, f.liters, 0)) AS liters_before,
       SUM(IF(f.month BETWEEN p.b1 AND p.e1, f.liters, 0)) AS liters_after
FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly` f CROSS JOIN periods p
GROUP BY p.comparison, f.family;

-- 5. Budget 2026 (forecast made with data to December 2025) against actual, months with actuals only
CREATE OR REPLACE VIEW `project-57338774-2b06-4ac1-ba9.liquor_market.m_budget_vs_actual` AS
WITH b AS (
  SELECT family, month,
         MAX(IF(measure = 'sales_usd', forecast_value, NULL)) AS budget_sales,
         MAX(IF(measure = 'liters', forecast_value, NULL)) AS budget_liters
  FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fc_budget_2026` GROUP BY family, month
)
SELECT b.family, b.month, b.budget_sales, b.budget_liters, a.sales_usd AS actual_sales, a.liters AS actual_liters
FROM b JOIN `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly` a USING (family, month);

-- 6. Outlook: 2026 = actual months + forecast for the rest; 2027 = forecast
CREATE OR REPLACE VIEW `project-57338774-2b06-4ac1-ba9.liquor_market.m_outlook_family` AS
WITH fc AS (
  SELECT family, month,
         MAX(IF(measure = 'sales_usd', forecast_value, NULL)) AS sales_usd,
         MAX(IF(measure = 'liters', forecast_value, NULL)) AS liters
  FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fc_outlook` GROUP BY family, month
),
allm AS (
  SELECT family, month, sales_usd, liters, 'actual' AS kind FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly`
  WHERE month >= '2025-01-01'
  UNION ALL
  SELECT family, month, sales_usd, liters, 'forecast' FROM fc
)
SELECT family, EXTRACT(YEAR FROM month) AS year,
       SUM(sales_usd) AS sales_usd, SUM(liters) AS liters,
       SUM(IF(kind = 'actual', sales_usd, 0)) AS actual_part_sales
FROM allm GROUP BY family, year;

-- 7. Seasonality: share of each calendar month in the year's sales, average of 2017-2025
CREATE OR REPLACE VIEW `project-57338774-2b06-4ac1-ba9.liquor_market.m_seasonality` AS
WITH m AS (
  SELECT EXTRACT(YEAR FROM month) AS y, EXTRACT(MONTH FROM month) AS mo, SUM(sales_usd) AS s
  FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly`
  WHERE month BETWEEN '2017-01-01' AND '2025-12-01' GROUP BY y, mo
),
sh AS (SELECT mo, s / SUM(s) OVER (PARTITION BY y) AS share FROM m)
SELECT mo AS month_of_year, AVG(share) AS avg_share, MIN(share) AS min_share, MAX(share) AS max_share
FROM sh GROUP BY mo;
