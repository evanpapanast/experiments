-- Step 1. Is there a new month? Reads the public source (about 0.8 GB, free tier).
-- Result saved as data/source_months.csv. If the newest month is already closed, the run stops here.
SELECT DATE_TRUNC(date, MONTH) AS month, COUNT(*) AS order_lines,
       ROUND(SUM(sale_dollars)) AS sales_usd, ROUND(SUM(volume_sold_liters)) AS liters, MAX(date) AS last_day
FROM `bigquery-public-data.iowa_liquor_sales.sales`
WHERE date >= '2026-03-01'
GROUP BY month ORDER BY month;
