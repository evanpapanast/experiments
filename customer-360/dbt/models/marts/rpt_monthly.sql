select format_date('%Y-%m', order_date) as month, purchase_channel as channel,
  round(sum(if({{ is_net() }}, sale_price, 0))) as net_revenue,
  round(sum(if({{ is_net() }}, sale_price - product_cost, 0))) as gross_margin
from {{ ref('stg_order_items') }}
group by 1, 2
