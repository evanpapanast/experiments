-- Customer 360 (TheLook) - step 1: GDPR-minimised staging tables.
-- Source: bigquery-public-data.thelook_ecommerce (fully synthetic data from Google's Looker team).
-- Window: 24 months, 20 Nov 2024 to 19 Nov 2026 (snapshot frozen on 19 Nov 2026; the source adds rows daily).
-- Data minimisation: only the columns below are copied. Names, email, street address, postal code, city, state,
-- latitude/longitude, exact age, IP address, browser and page URL never leave the public dataset.
-- Customers under 18 are excluded entirely (children's data gets extra protection under GDPR Art. 8).

CREATE SCHEMA IF NOT EXISTS `project-57338774-2b06-4ac1-ba9.customer_360`
OPTIONS (location = 'US', description = 'Customer 360 experiment on TheLook synthetic e-commerce data. GDPR-minimised.');

-- Customers: ID plus coarse attributes only.
CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.customer_360.stg_customers` AS
SELECT
  id AS customer_id,
  CASE WHEN age < 25 THEN '18-24' WHEN age < 35 THEN '25-34' WHEN age < 45 THEN '35-44'
       WHEN age < 55 THEN '45-54' ELSE '55-70' END AS age_band,
  IF(gender = 'M', 'Men', 'Women') AS gender,
  CASE
    WHEN country IN ('China', 'South Korea', 'Japan', 'Australia') THEN 'Asia-Pacific'
    WHEN country = 'United States' THEN 'North America'
    WHEN country IN ('Brasil', 'Colombia') THEN 'Latin America'
    ELSE 'Europe' END AS region,               -- country itself is not stored (small countries could single people out)
  traffic_source AS acquisition_channel,       -- how the customer first found the shop
  DATE_TRUNC(DATE(created_at), MONTH) AS signup_month
FROM `bigquery-public-data.thelook_ecommerce.users`
WHERE age >= 18 AND DATE(created_at) <= DATE '2026-11-19';

-- Website visits: one row per session, with the channel and how far the visit got.
CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.customer_360.stg_sessions` AS
SELECT
  e.session_id,
  ANY_VALUE(e.user_id) AS customer_id,         -- NULL for visitors who were not logged in
  MIN(DATE(e.created_at)) AS session_date,
  CASE ANY_VALUE(e.traffic_source) WHEN 'Adwords' THEN 'Google Ads' ELSE ANY_VALUE(e.traffic_source) END AS channel,
  LOGICAL_OR(e.event_type = 'product') AS reached_product,
  LOGICAL_OR(e.event_type = 'cart') AS reached_cart,
  LOGICAL_OR(e.event_type = 'purchase') AS purchased
FROM `bigquery-public-data.thelook_ecommerce.events` e
WHERE e.created_at >= TIMESTAMP('2024-11-20') AND e.created_at < TIMESTAMP('2026-11-20')
GROUP BY e.session_id
HAVING ANY_VALUE(e.user_id) IS NULL
    OR ANY_VALUE(e.user_id) IN (SELECT customer_id FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_customers`);

-- Order lines with real product cost and the channel of the purchase visit
-- (nearest purchase event of the same customer within 24 hours of the order).
CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.customer_360.stg_order_items` AS
WITH oi AS (
  SELECT i.id AS order_item_id, i.order_id, i.user_id AS customer_id, i.created_at, i.status,
         p.category, p.department, i.sale_price, ii.cost
  FROM `bigquery-public-data.thelook_ecommerce.order_items` i
  JOIN `bigquery-public-data.thelook_ecommerce.inventory_items` ii ON ii.id = i.inventory_item_id
  JOIN `bigquery-public-data.thelook_ecommerce.products` p ON p.id = i.product_id
  WHERE i.created_at >= TIMESTAMP('2024-11-20') AND i.created_at < TIMESTAMP('2026-11-20')
    AND i.user_id IN (SELECT customer_id FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_customers`)
),
ord AS (SELECT DISTINCT order_id, customer_id, MIN(created_at) OVER (PARTITION BY order_id) AS order_ts FROM oi),
att AS (
  SELECT o.order_id,
    ARRAY_AGG(CASE e.traffic_source WHEN 'Adwords' THEN 'Google Ads' ELSE e.traffic_source END
      ORDER BY ABS(TIMESTAMP_DIFF(e.created_at, o.order_ts, SECOND)) LIMIT 1)[OFFSET(0)] AS purchase_channel
  FROM ord o
  JOIN `bigquery-public-data.thelook_ecommerce.events` e
    ON e.user_id = o.customer_id AND e.event_type = 'purchase'
   AND ABS(TIMESTAMP_DIFF(e.created_at, o.order_ts, MINUTE)) <= 1440
  GROUP BY o.order_id
)
SELECT oi.order_item_id, oi.order_id, oi.customer_id, DATE(oi.created_at) AS order_date, oi.status,
  oi.category, oi.department, ROUND(oi.sale_price, 2) AS sale_price, ROUND(oi.cost, 2) AS product_cost,
  COALESCE(att.purchase_channel, 'Unattributed') AS purchase_channel
FROM oi LEFT JOIN att USING (order_id);
