-- Customer 360 (TheLook) - step 3: group-level reporting tables. No customer IDs leave this step.
-- Any cell with fewer than 50 customers is suppressed (set to NULL).

CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.customer_360.rpt_segments` AS
SELECT segment, COUNT(*) customers, ROUND(SUM(net_revenue)) net_revenue, ROUND(SUM(net_revenue - net_cost)) gross_margin,
  ROUND(SUM(returned_value)) returned_value, ROUND(SUM(gross_sales)) gross_sales, SUM(orders) orders,
  ROUND(SUM(net_revenue_12m)) net_revenue_12m
FROM `project-57338774-2b06-4ac1-ba9.customer_360.customer_metrics` GROUP BY 1;

CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.customer_360.rpt_segment_channel` AS
SELECT segment, preferred_channel,
  IF(COUNT(*) < 50, NULL, COUNT(*)) customers, IF(COUNT(*) < 50, NULL, ROUND(SUM(net_revenue))) net_revenue,
  COUNT(*) < 50 AS suppressed
FROM `project-57338774-2b06-4ac1-ba9.customer_360.customer_metrics` GROUP BY 1, 2;

CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.customer_360.rpt_channel_purchase` AS
SELECT purchase_channel AS channel,
  COUNT(DISTINCT IF(status != 'Cancelled', order_id, NULL)) orders,
  COUNT(DISTINCT IF(status != 'Cancelled', customer_id, NULL)) customers,
  ROUND(SUM(IF(status != 'Cancelled', sale_price, 0))) gross_sales,
  ROUND(SUM(IF(status NOT IN ('Cancelled', 'Returned'), sale_price, 0))) net_revenue,
  ROUND(SUM(IF(status NOT IN ('Cancelled', 'Returned'), product_cost, 0))) product_cost,
  ROUND(SUM(IF(status = 'Returned', sale_price, 0))) returned_value,
  ROUND(SUM(IF(status = 'Cancelled', sale_price, 0))) cancelled_value
FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_order_items` GROUP BY 1;

CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.customer_360.rpt_channel_acquisition` AS
SELECT acquisition_channel AS channel, COUNT(*) registered, COUNTIF(orders > 0) buyers, COUNTIF(orders >= 2) repeat_buyers,
  ROUND(SUM(net_revenue)) net_revenue, ROUND(SUM(net_revenue - net_cost)) gross_margin,
  ROUND(SUM(returned_value)) returned_value, ROUND(SUM(gross_sales)) gross_sales
FROM `project-57338774-2b06-4ac1-ba9.customer_360.customer_metrics` GROUP BY 1;

CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.customer_360.rpt_funnel` AS
SELECT channel, COUNT(*) sessions, COUNTIF(reached_product) product, COUNTIF(reached_cart) cart,
  COUNTIF(purchased) purchase, COUNTIF(customer_id IS NULL) anonymous_sessions
FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_sessions` GROUP BY 1;

CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.customer_360.rpt_monthly` AS
SELECT FORMAT_DATE('%Y-%m', order_date) month, purchase_channel channel,
  ROUND(SUM(IF(status NOT IN ('Cancelled', 'Returned'), sale_price, 0))) net_revenue,
  ROUND(SUM(IF(status NOT IN ('Cancelled', 'Returned'), sale_price - product_cost, 0))) gross_margin
FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_order_items` GROUP BY 1, 2;

CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.customer_360.rpt_demographics` AS
SELECT 'region' dim, region val, COUNT(*) customers, COUNTIF(orders > 0) buyers, ROUND(SUM(net_revenue)) net_revenue,
  ROUND(SUM(net_revenue - net_cost)) gross_margin, ROUND(SUM(returned_value)) returned_value, ROUND(SUM(gross_sales)) gross_sales
FROM `project-57338774-2b06-4ac1-ba9.customer_360.customer_metrics` GROUP BY 1, 2
UNION ALL SELECT 'age_band', age_band, COUNT(*), COUNTIF(orders > 0), ROUND(SUM(net_revenue)), ROUND(SUM(net_revenue - net_cost)),
  ROUND(SUM(returned_value)), ROUND(SUM(gross_sales)) FROM `project-57338774-2b06-4ac1-ba9.customer_360.customer_metrics` GROUP BY 1, 2
UNION ALL SELECT 'gender', gender, COUNT(*), COUNTIF(orders > 0), ROUND(SUM(net_revenue)), ROUND(SUM(net_revenue - net_cost)),
  ROUND(SUM(returned_value)), ROUND(SUM(gross_sales)) FROM `project-57338774-2b06-4ac1-ba9.customer_360.customer_metrics` GROUP BY 1, 2;

CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.customer_360.rpt_region_channel` AS
SELECT region, preferred_channel, COUNT(*) customers
FROM `project-57338774-2b06-4ac1-ba9.customer_360.customer_metrics` WHERE orders > 0 GROUP BY 1, 2;

CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.customer_360.rpt_category` AS
SELECT category, department,
  ROUND(SUM(IF(status NOT IN ('Cancelled', 'Returned'), sale_price, 0))) net_revenue,
  ROUND(SUM(IF(status NOT IN ('Cancelled', 'Returned'), sale_price - product_cost, 0))) gross_margin,
  ROUND(SUM(IF(status = 'Returned', sale_price, 0))) returned_value,
  ROUND(SUM(IF(status != 'Cancelled', sale_price, 0))) gross_sales
FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_order_items` GROUP BY 1, 2;
