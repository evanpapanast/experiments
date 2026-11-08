-- Compact extracts copied into data/bigquery_extract.txt (one block per query).
-- Each returns rows as 'a|b|c' joined with ';' so the result is a single cell.
SELECT
 (SELECT STRING_AGG(FORMAT('%d|%s|%.0f|%.0f|%.0f', year, family, sales_usd, cost_usd, liters), ';' ORDER BY year, family)
  FROM `project-57338774-2b06-4ac1-ba9.liquor_market.m_year_family`) AS year_family,
 (SELECT STRING_AGG(FORMAT('%t|%.0f|%.0f|%.0f', month, sales_usd, cost_usd, liters), ';' ORDER BY month)
  FROM `project-57338774-2b06-4ac1-ba9.liquor_market.m_month_total`) AS month_total,
 (SELECT STRING_AGG(FORMAT('%d|%.5f|%.5f|%.5f', month_of_year, avg_share, min_share, max_share), ';' ORDER BY month_of_year)
  FROM `project-57338774-2b06-4ac1-ba9.liquor_market.m_seasonality`) AS seasonality,
 (SELECT STRING_AGG(FORMAT('%t|%.0f|%.0f|%.0f|%.0f', month, b_s, b_l, a_s, a_l), ';' ORDER BY month)
  FROM (SELECT month, SUM(budget_sales) b_s, SUM(budget_liters) b_l, SUM(actual_sales) a_s, SUM(actual_liters) a_l
        FROM `project-57338774-2b06-4ac1-ba9.liquor_market.m_budget_vs_actual` GROUP BY month)) AS budget_vs_actual_month,
 (SELECT STRING_AGG(FORMAT('%s|%.0f|%.0f|%.0f|%.0f', family, b_s, b_l, a_s, a_l), ';' ORDER BY family)
  FROM (SELECT family, SUM(budget_sales) b_s, SUM(budget_liters) b_l, SUM(actual_sales) a_s, SUM(actual_liters) a_l
        FROM `project-57338774-2b06-4ac1-ba9.liquor_market.m_budget_vs_actual` GROUP BY family)) AS budget_vs_actual_family,
 (SELECT STRING_AGG(FORMAT('%s|%.0f|%.0f', family, s, l), ';')
  FROM (SELECT family, SUM(IF(measure='sales_usd', forecast_value, 0)) s, SUM(IF(measure='liters', forecast_value, 0)) l
        FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fc_budget_2026` GROUP BY family)) AS budget_2026_family,
 (SELECT STRING_AGG(FORMAT('%s|%s|%.0f|%.0f|%.0f|%.0f', comparison, family, sales_before, sales_after, liters_before, liters_after), ';' ORDER BY comparison, family)
  FROM `project-57338774-2b06-4ac1-ba9.liquor_market.m_pvm_family`) AS pvm_family,
 (SELECT STRING_AGG(FORMAT('%s|%d|%.0f|%.0f', family, year, sales_usd, liters), ';' ORDER BY family, year)
  FROM `project-57338774-2b06-4ac1-ba9.liquor_market.m_outlook_family`) AS outlook_family,
 (SELECT STRING_AGG(FORMAT('%s|%t|%.0f|%.0f|%.0f', measure, month, fv, lo, hi), ';' ORDER BY measure, month)
  FROM (SELECT measure, month, SUM(forecast_value) fv, SUM(lower_80) lo, SUM(upper_80) hi
        FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fc_outlook` GROUP BY measure, month)) AS outlook_month_sum,
 (SELECT STRING_AGG(FORMAT('%s|%t|%.0f|%.0f|%.0f', version, month, ROUND(forecast_value / 1e4) * 1e4, ROUND(lower_80 / 1e4) * 1e4, ROUND(upper_80 / 1e4) * 1e4), ';' ORDER BY version, month)
  FROM `project-57338774-2b06-4ac1-ba9.liquor_market.fc_total`) AS forecast_total;
