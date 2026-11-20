-- Customer 360 (TheLook) - step 4: 15 data-quality and privacy checks inside BigQuery.
-- Results (all passed on 2026-11-20) are in data/bigquery_extract.json -> qa_bigquery and data_quality/dq_report.md.

CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.customer_360.qa_checks` AS
WITH src_users AS (SELECT COUNT(*) n FROM `bigquery-public-data.thelook_ecommerce.users` WHERE age >= 18 AND DATE(created_at) <= '2026-11-19'),
src_items AS (
  SELECT ROUND(SUM(IF(i.status NOT IN ('Cancelled', 'Returned'), i.sale_price, 0)), 0) net, COUNT(*) n
  FROM `bigquery-public-data.thelook_ecommerce.order_items` i JOIN `bigquery-public-data.thelook_ecommerce.users` u ON u.id = i.user_id
  WHERE i.created_at >= TIMESTAMP('2024-11-20') AND i.created_at < TIMESTAMP('2026-11-20') AND u.age >= 18 AND DATE(u.created_at) <= '2026-11-19'),
stg AS (SELECT ROUND(SUM(IF(status NOT IN ('Cancelled', 'Returned'), sale_price, 0)), 0) net, COUNT(*) n, COUNT(DISTINCT order_item_id) d,
  MIN(order_date) mn, MAX(order_date) mx, COUNTIF(purchase_channel = 'Unattributed') un, COUNTIF(sale_price <= 0 OR product_cost <= 0) badp,
  COUNTIF(customer_id NOT IN (SELECT customer_id FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_customers`)) orphan
  FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_order_items`),
pii AS (SELECT COUNT(*) n FROM `project-57338774-2b06-4ac1-ba9.customer_360.INFORMATION_SCHEMA.COLUMNS`
  WHERE LOWER(column_name) IN ('first_name', 'last_name', 'email', 'street_address', 'postal_code', 'city', 'state', 'latitude',
                               'longitude', 'ip_address', 'browser', 'uri', 'age', 'user_geom', 'country')),
small AS (
  SELECT COUNTIF(customers < 50) n FROM (
    SELECT customers FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_segments`
    UNION ALL SELECT customers FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_segment_channel` WHERE NOT suppressed
    UNION ALL SELECT customers FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_region_channel`
    UNION ALL SELECT customers FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_demographics`
    UNION ALL SELECT registered FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_channel_acquisition`
    UNION ALL SELECT customers FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_channel_purchase`)),
seg AS (SELECT (SELECT SUM(customers) FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_segments`) a,
               (SELECT COUNT(*) FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_customers`) b,
               (SELECT SUM(net_revenue) FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_segments`) r1,
               (SELECT SUM(net_revenue) FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_channel_purchase`) r2),
dupc AS (SELECT COUNT(*) - COUNT(DISTINCT customer_id) n FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_customers`),
sess AS (SELECT MIN(session_date) mn, MAX(session_date) mx, COUNT(*) - COUNT(DISTINCT session_id) dup
         FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_sessions`)
SELECT * FROM UNNEST([
 STRUCT('Privacy' AS area, 'No personal-data columns (names, email, address, postcode, city, IP, browser, exact age, GPS, country)' AS check_name,
        CAST((SELECT n FROM pii) AS STRING) AS result, (SELECT n FROM pii) = 0 AS passed),
 ('Privacy', 'Only adults (18+) included: customer count matches source adults',
   CONCAT((SELECT CAST(COUNT(*) AS STRING) FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_customers`), ' vs ', (SELECT CAST(n AS STRING) FROM src_users)),
   (SELECT COUNT(*) FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_customers`) = (SELECT n FROM src_users)),
 ('Privacy', 'Every published group has 50+ customers (smaller cells suppressed)', CAST((SELECT n FROM small) AS STRING), (SELECT n FROM small) = 0),
 ('Completeness', 'Order lines reconcile to source', CONCAT(CAST((SELECT n FROM stg) AS STRING), ' vs ', CAST((SELECT n FROM src_items) AS STRING)),
   (SELECT n FROM stg) = (SELECT n FROM src_items)),
 ('Accuracy', 'Net revenue reconciles to source', CONCAT(CAST((SELECT net FROM stg) AS STRING), ' vs ', CAST((SELECT net FROM src_items) AS STRING)),
   ABS((SELECT net FROM stg) - (SELECT net FROM src_items)) <= 1),
 ('Accuracy', 'Segment revenue = channel revenue (two views agree)', CONCAT(CAST(ROUND((SELECT r1 FROM seg)) AS STRING), ' vs ', CAST(ROUND((SELECT r2 FROM seg)) AS STRING)),
   ABS((SELECT r1 FROM seg) - (SELECT r2 FROM seg)) <= 10),
 ('Completeness', 'Every customer is in exactly one segment', CONCAT(CAST((SELECT a FROM seg) AS STRING), ' vs ', CAST((SELECT b FROM seg) AS STRING)),
   (SELECT a FROM seg) = (SELECT b FROM seg)),
 ('Uniqueness', 'No duplicate order lines', CAST((SELECT n - d FROM stg) AS STRING), (SELECT n - d FROM stg) = 0),
 ('Uniqueness', 'No duplicate customers', CAST((SELECT n FROM dupc) AS STRING), (SELECT n FROM dupc) = 0),
 ('Uniqueness', 'No duplicate sessions', CAST((SELECT dup FROM sess) AS STRING), (SELECT dup FROM sess) = 0),
 ('Validity', 'Order dates inside 20 Nov 2024 - 19 Nov 2026', CONCAT(CAST((SELECT mn FROM stg) AS STRING), ' to ', CAST((SELECT mx FROM stg) AS STRING)),
   (SELECT mn FROM stg) >= '2024-11-20' AND (SELECT mx FROM stg) <= '2026-11-19'),
 ('Validity', 'Session dates inside window', CONCAT(CAST((SELECT mn FROM sess) AS STRING), ' to ', CAST((SELECT mx FROM sess) AS STRING)),
   (SELECT mn FROM sess) >= '2024-11-20' AND (SELECT mx FROM sess) <= '2026-11-19'),
 ('Validity', 'Prices and product costs are positive', CAST((SELECT badp FROM stg) AS STRING), (SELECT badp FROM stg) = 0),
 ('Integrity', 'Every order line links to a known customer', CAST((SELECT orphan FROM stg) AS STRING), (SELECT orphan FROM stg) = 0),
 ('Integrity', 'Orders linked to a purchase visit (channel known)', CONCAT(CAST((SELECT un FROM stg) AS STRING), ' unattributed lines'), (SELECT un FROM stg) = 0)
]);
