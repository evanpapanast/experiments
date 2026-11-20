select acquisition_channel as channel, count(*) as registered, countif(orders > 0) as buyers, countif(orders >= 2) as repeat_buyers,
  round(sum(net_revenue)) as net_revenue, round(sum(net_revenue - net_cost)) as gross_margin,
  round(sum(returned_value)) as returned_value, round(sum(gross_sales)) as gross_sales
from {{ ref('int_customer_metrics') }}
group by 1
