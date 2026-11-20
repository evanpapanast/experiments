select segment, count(*) as customers, round(sum(net_revenue)) as net_revenue, round(sum(net_revenue - net_cost)) as gross_margin,
  round(sum(returned_value)) as returned_value, round(sum(gross_sales)) as gross_sales, sum(orders) as orders,
  round(sum(net_revenue_12m)) as net_revenue_12m
from {{ ref('int_customer_metrics') }}
group by 1
