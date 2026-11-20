select purchase_channel as channel,
  count(distinct if({{ is_shipped() }}, order_id, null)) as orders,
  count(distinct if({{ is_shipped() }}, customer_id, null)) as customers,
  round(sum(if({{ is_shipped() }}, sale_price, 0))) as gross_sales,
  round(sum(if({{ is_net() }}, sale_price, 0))) as net_revenue,
  round(sum(if({{ is_net() }}, product_cost, 0))) as product_cost,
  round(sum(if(status = 'Returned', sale_price, 0))) as returned_value,
  round(sum(if(status = 'Cancelled', sale_price, 0))) as cancelled_value
from {{ ref('stg_order_items') }}
group by 1
