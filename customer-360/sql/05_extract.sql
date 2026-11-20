-- Customer 360 (TheLook) - step 5: compact extract of the group-level tables for the report.
-- Each row returns one table as a JSON array; saved as data/bigquery_extract.json.
SELECT 'segments' t, TO_JSON_STRING(ARRAY_AGG(s)) j FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_segments` s
UNION ALL SELECT 'segment_channel', TO_JSON_STRING(ARRAY_AGG(STRUCT(s.segment, s.preferred_channel, s.customers, s.net_revenue)))
  FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_segment_channel` s
UNION ALL SELECT 'channel_purchase', TO_JSON_STRING(ARRAY_AGG(s)) FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_channel_purchase` s
UNION ALL SELECT 'channel_acquisition', TO_JSON_STRING(ARRAY_AGG(s)) FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_channel_acquisition` s
UNION ALL SELECT 'funnel', TO_JSON_STRING(ARRAY_AGG(s)) FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_funnel` s
UNION ALL SELECT 'demographics', TO_JSON_STRING(ARRAY_AGG(s)) FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_demographics` s
UNION ALL SELECT 'region_channel', TO_JSON_STRING(ARRAY_AGG(s)) FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_region_channel` s
UNION ALL SELECT 'category', TO_JSON_STRING(ARRAY_AGG(s ORDER BY net_revenue DESC)) FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_category` s
UNION ALL SELECT 'monthly', TO_JSON_STRING(ARRAY_AGG(STRUCT(month AS m, channel AS c, net_revenue AS r, gross_margin AS g) ORDER BY month, channel))
  FROM `project-57338774-2b06-4ac1-ba9.customer_360.rpt_monthly`
UNION ALL SELECT 'repeat_by_first_channel', TO_JSON_STRING(ARRAY_AGG(x)) FROM (
  SELECT purchase_channel AS channel, COUNT(*) first_buyers, COUNTIF(n >= 2) repeaters FROM (
    SELECT customer_id, ARRAY_AGG(purchase_channel ORDER BY order_date, order_id LIMIT 1)[OFFSET(0)] purchase_channel, COUNT(DISTINCT order_id) n
    FROM `project-57338774-2b06-4ac1-ba9.customer_360.stg_order_items` WHERE status != 'Cancelled' GROUP BY 1) GROUP BY 1) x
UNION ALL SELECT 'qa_bigquery', TO_JSON_STRING(ARRAY_AGG(STRUCT(area, check_name AS `check`, result, passed)))
  FROM `project-57338774-2b06-4ac1-ba9.customer_360.qa_checks`;
