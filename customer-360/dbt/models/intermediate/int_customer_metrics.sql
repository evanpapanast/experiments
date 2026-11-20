-- One internal row per customer ID: totals, preferred channel and customer group. Never published.
with o as (
  select customer_id,
    count(distinct if({{ is_shipped() }}, order_id, null)) as orders,
    sum(if({{ is_net() }}, sale_price, 0)) as net_revenue,
    sum(if({{ is_net() }}, product_cost, 0)) as net_cost,
    sum(if(status = 'Returned', sale_price, 0)) as returned_value,
    sum(if({{ is_shipped() }}, sale_price, 0)) as gross_sales,
    min(if({{ is_shipped() }}, order_date, null)) as first_order,
    max(if({{ is_shipped() }}, order_date, null)) as last_order,
    sum(if({{ is_net() }} and order_date > date '{{ var("last_12m_after") }}', sale_price, 0)) as net_revenue_12m
  from {{ ref('stg_order_items') }}
  group by 1
),
s as (
  select customer_id, channel, count(*) as n, max(session_start) as last_ts
  from {{ ref('stg_sessions') }} where customer_id is not null group by 1, 2
),
pref as (  -- preferred channel = channel of most visits; ties: most recent visit, then channel name (strict order, so every run gives the same answer)
  select customer_id, array_agg(channel order by n desc, last_ts desc, channel limit 1)[offset(0)] as preferred_channel, sum(n) as sessions
  from s group by 1
),
bought_before as (  -- lets us split "Lapsed" from "Never bought"
  select distinct user_id as customer_id from {{ source('thelook', 'order_items') }}
  where created_at < timestamp('{{ var("window_start") }}') and status != 'Cancelled'
)
select c.*,
  coalesce(o.orders, 0) as orders, coalesce(o.net_revenue, 0) as net_revenue, coalesce(o.net_cost, 0) as net_cost,
  coalesce(o.returned_value, 0) as returned_value, coalesce(o.gross_sales, 0) as gross_sales,
  coalesce(o.net_revenue_12m, 0) as net_revenue_12m, o.first_order, o.last_order,
  date_diff(date '{{ var("snapshot_date") }}', o.last_order, day) as recency_days,
  coalesce(p.preferred_channel, 'No visits') as preferred_channel, coalesce(p.sessions, 0) as sessions,
  case
    when coalesce(o.orders, 0) = 0 and b.customer_id is not null then 'Lapsed'
    when coalesce(o.orders, 0) = 0 then 'Never bought'
    when o.orders >= 3 and date_diff(date '{{ var("snapshot_date") }}', o.last_order, day) <= 180 then 'Champions'
    when o.orders = 2 and date_diff(date '{{ var("snapshot_date") }}', o.last_order, day) <= 180 then 'Loyal'
    when o.orders >= 2 then 'At risk'
    when date_diff(date '{{ var("snapshot_date") }}', o.first_order, day) <= 90 then 'New'
    else 'One-time buyers' end as segment
from {{ ref('stg_customers') }} c
left join o using (customer_id)
left join pref p using (customer_id)
left join bought_before b using (customer_id)
