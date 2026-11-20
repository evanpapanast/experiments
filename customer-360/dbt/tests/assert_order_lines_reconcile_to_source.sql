-- Completeness and accuracy: order lines and net revenue match the public source exactly.
with src as (
  select count(*) as n, round(sum(if(i.status not in ('Cancelled', 'Returned'), i.sale_price, 0))) as net
  from {{ source('thelook', 'order_items') }} i
  join {{ source('thelook', 'users') }} u on u.id = i.user_id
  where {{ window_filter('i.created_at') }}
    and u.age >= {{ var('min_age') }} and date(u.created_at) <= date '{{ var("snapshot_date") }}'
),
mdl as (
  select count(*) as n, round(sum(if({{ is_net() }}, sale_price, 0))) as net from {{ ref('stg_order_items') }}
)
select * from src, mdl where src.n != mdl.n or abs(src.net - mdl.net) > 1
