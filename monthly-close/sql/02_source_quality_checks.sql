-- Step 2. Quality checks on the order lines of the month being closed and the month before (about 2.8 GB, free tier).
-- Result saved as data/source_checks.csv.
WITH m AS (
  SELECT s.*, c.family
  FROM `bigquery-public-data.iowa_liquor_sales.sales` s
  LEFT JOIN `project-57338774-2b06-4ac1-ba9.liquor_market.dim_category` c USING (category_name)
  WHERE s.date BETWEEN '2026-03-01' AND '2026-04-30')
SELECT DATE_TRUNC(date, MONTH) AS month,
  COUNT(*) AS order_lines,
  COUNTIF(sale_dollars IS NULL OR volume_sold_liters IS NULL OR category_name IS NULL) AS missing_key_fields,
  COUNTIF(sale_dollars < 0) AS credit_lines,
  COUNT(*) - COUNT(DISTINCT invoice_and_item_number) AS duplicate_invoice_lines,
  COUNTIF(ABS(sale_dollars - bottles_sold * state_bottle_retail) > 0.05) AS sale_not_bottles_x_price,
  COUNTIF(category_name IS NOT NULL AND family IS NULL) AS unmapped_lines,
  COUNTIF(SAFE_DIVIDE(sale_dollars, volume_sold_liters) > 500) AS price_per_litre_over_500,
  COUNT(DISTINCT date) AS trading_days,
  ROUND(1 - SUM(bottles_sold * state_bottle_cost) / SUM(sale_dollars), 4) AS gross_margin
FROM m GROUP BY month ORDER BY month;

-- Follow-up on the price-per-litre warning (about 1.1 GB). Result saved as data/price_outliers.csv.
SELECT CASE WHEN bottle_volume_ml <= 100 THEN 'up to 100ml'
            WHEN bottle_volume_ml <= 375 THEN '101-375ml' ELSE 'over 375ml' END AS bottle_size,
       COUNT(*) AS order_lines, ROUND(SUM(sale_dollars)) AS sales_usd
FROM `bigquery-public-data.iowa_liquor_sales.sales`
WHERE date BETWEEN '2026-04-01' AND '2026-04-30' AND SAFE_DIVIDE(sale_dollars, volume_sold_liters) > 500
GROUP BY bottle_size ORDER BY order_lines DESC;
