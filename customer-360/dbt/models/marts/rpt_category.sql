select category, department,
  round(sum(if({{ is_net() }}, sale_price, 0))) as net_revenue,
  round(sum(if({{ is_net() }}, sale_price - product_cost, 0))) as gross_margin,
  round(sum(if(status = 'Returned', sale_price, 0))) as returned_value,
  round(sum(if({{ is_shipped() }}, sale_price, 0))) as gross_sales
from {{ ref('stg_order_items') }}
group by 1, 2
