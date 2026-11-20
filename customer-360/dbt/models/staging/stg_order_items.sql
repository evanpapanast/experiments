-- Order lines with real product cost and the channel of the purchase visit
-- (nearest purchase event of the same customer within 24 hours of the order).
with oi as (
  select i.id as order_item_id, i.order_id, i.user_id as customer_id, i.created_at, i.status,
         p.category, p.department, i.sale_price, ii.cost
  from {{ source('thelook', 'order_items') }} i
  join {{ source('thelook', 'inventory_items') }} ii on ii.id = i.inventory_item_id
  join {{ source('thelook', 'products') }} p on p.id = i.product_id
  where {{ window_filter('i.created_at') }}
    and i.user_id in (select customer_id from {{ ref('stg_customers') }})
),
ord as (
  select distinct order_id, customer_id, min(created_at) over (partition by order_id) as order_ts from oi
),
att as (
  select o.order_id,
    array_agg({{ channel_name('e.traffic_source') }}
      order by abs(timestamp_diff(e.created_at, o.order_ts, second)), e.created_at, e.traffic_source limit 1)[offset(0)] as purchase_channel  -- full tie-break: same result on every run
  from ord o
  join {{ source('thelook', 'events') }} e
    on e.user_id = o.customer_id and e.event_type = 'purchase'
   and abs(timestamp_diff(e.created_at, o.order_ts, minute)) <= 1440
  group by o.order_id
)
select oi.order_item_id, oi.order_id, oi.customer_id, date(oi.created_at) as order_date, oi.status,
  oi.category, oi.department, round(oi.sale_price, 2) as sale_price, round(oi.cost, 2) as product_cost,
  coalesce(att.purchase_channel, 'Unattributed') as purchase_channel
from oi left join att using (order_id)
