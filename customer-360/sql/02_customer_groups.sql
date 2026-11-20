-- Customer 360 (TheLook) - step 2: one internal row per customer ID, used only to assign each customer to a group.
-- This table is never published. The report only shows group totals with at least 50 customers.
-- Snapshot date: 19 Nov 2026. Revenue = net revenue (excludes cancelled and returned lines).

CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.customer_360.customer_metrics` AS
WITH o AS (
  SELECT customer_id,
    COUNT(DISTINCT IF(status != 'Cancelled', order_id, NULL)) AS orders,
    SUM(IF(status NOT IN ('Cancelled', 'Returned'), sale_price, 0)) AS net_revenue,
    SUM(IF(status NOT IN ('Cancelled', 'Returned'), product_cost, 0)) AS net_cost,
    SUM(IF(status = 'Returned', sale_price, 0)) AS returned_value,
    SUM(IF(status != 'Cancelled', sale_price, 0)) AS gross_sales,
    MIN(IF(status != 'Cancelled', order_date, NULL)) AS first_order,
    MAX(IF(status != 'Cancelled', order_date, NULL)) AS last_order,
    SUM(IF(status NOT IN ('Cancelled', 'Returned') AND order_date > DATE '2025-11-19', sale_price, 0)) AS net_revenue_12m
  FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_order_items` GROUP BY 1),
s AS (
  SELECT customer_id, channel, COUNT(*) AS n, MAX(session_date) AS last_d
  FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_sessions` WHERE customer_id IS NOT NULL GROUP BY 1, 2),
pref AS (  -- preferred channel = the channel of most visits (ties: most recent)
  SELECT customer_id, ARRAY_AGG(channel ORDER BY n DESC, last_d DESC LIMIT 1)[OFFSET(0)] AS preferred_channel, SUM(n) AS sessions
  FROM s GROUP BY 1),
before AS (  -- bought before the window: lets us split "Lapsed" from "Never bought"
  SELECT DISTINCT user_id AS customer_id FROM `bigquery-public-data.thelook_ecommerce.order_items`
  WHERE created_at < TIMESTAMP('2024-11-20') AND status != 'Cancelled')
SELECT c.*,
  COALESCE(o.orders, 0) AS orders, COALESCE(o.net_revenue, 0) AS net_revenue, COALESCE(o.net_cost, 0) AS net_cost,
  COALESCE(o.returned_value, 0) AS returned_value, COALESCE(o.gross_sales, 0) AS gross_sales,
  COALESCE(o.net_revenue_12m, 0) AS net_revenue_12m, o.first_order, o.last_order,
  DATE_DIFF(DATE '2026-11-19', o.last_order, DAY) AS recency_days,
  COALESCE(p.preferred_channel, 'No visits') AS preferred_channel, COALESCE(p.sessions, 0) AS sessions,
  CASE
    WHEN COALESCE(o.orders, 0) = 0 AND b.customer_id IS NOT NULL THEN 'Lapsed'          -- bought before, not in the last 24 months
    WHEN COALESCE(o.orders, 0) = 0 THEN 'Never bought'                                   -- registered, never bought
    WHEN o.orders >= 3 AND DATE_DIFF(DATE '2026-11-19', o.last_order, DAY) <= 180 THEN 'Champions'
    WHEN o.orders = 2 AND DATE_DIFF(DATE '2026-11-19', o.last_order, DAY) <= 180 THEN 'Loyal'
    WHEN o.orders >= 2 THEN 'At risk'                                                    -- repeat buyer, silent for 6+ months
    WHEN DATE_DIFF(DATE '2026-11-19', o.first_order, DAY) <= 90 THEN 'New'               -- first order in last 90 days
    ELSE 'One-time buyers' END AS segment
FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_customers` c
LEFT JOIN o USING (customer_id) LEFT JOIN pref p USING (customer_id) LEFT JOIN before b USING (customer_id);
