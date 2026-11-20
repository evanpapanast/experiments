-- Website visits: one row per session with channel and how far the visit got.
-- IP address, city, state, postal code, browser and page URL are not selected.
select
  e.session_id,
  any_value(e.user_id) as customer_id,          -- null for visitors who were not logged in
  min(date(e.created_at)) as session_date,
  min(e.created_at) as session_start,           -- exact time, used only to break ties deterministically
  {{ channel_name('any_value(e.traffic_source)') }} as channel,
  logical_or(e.event_type = 'product') as reached_product,
  logical_or(e.event_type = 'cart') as reached_cart,
  logical_or(e.event_type = 'purchase') as purchased
from {{ source('thelook', 'events') }} e
where {{ window_filter('e.created_at') }}
group by e.session_id
having any_value(e.user_id) is null
    or any_value(e.user_id) in (select customer_id from {{ ref('stg_customers') }})
