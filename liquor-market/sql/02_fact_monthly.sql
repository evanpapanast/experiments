-- Monthly sales by product family, from January 2017 (consistent category names).
-- Aggregated in BigQuery straight from the public table; no store, supplier or product names are kept.
-- sales   = what stores paid the state wholesaler (state bottle retail x bottles)
-- cost    = what the wholesaler paid suppliers (state bottle cost x bottles)
-- margin  = sales - cost (the wholesaler's gross margin)
CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.liquor_market.fact_monthly` AS
SELECT
  DATE_TRUNC(s.date, MONTH)                         AS month,
  COALESCE(c.family, 'Gift packs & other')          AS family,
  COUNT(*)                                          AS order_lines,
  COUNTIF(s.sale_dollars < 0)                       AS credit_lines,
  ROUND(SUM(s.sale_dollars), 2)                     AS sales_usd,
  ROUND(SUM(s.state_bottle_cost * s.bottles_sold), 2) AS cost_usd,
  ROUND(SUM(s.volume_sold_liters), 2)               AS liters,
  SUM(s.bottles_sold)                               AS bottles
FROM `bigquery-public-data.iowa_liquor_sales.sales` AS s
LEFT JOIN `project-57338774-2b06-4ac1-ba9.liquor_market.dim_category` AS c
  ON c.category_name = s.category_name
WHERE s.date >= '2017-01-01'
GROUP BY month, family
