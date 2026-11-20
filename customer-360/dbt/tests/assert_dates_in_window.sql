-- Validity: nothing outside the 24-month window.
select 'order' as kind, order_date as d from {{ ref('stg_order_items') }}
where order_date < date '{{ var("window_start") }}' or order_date > date '{{ var("snapshot_date") }}'
union all
select 'session', session_date from {{ ref('stg_sessions') }}
where session_date < date '{{ var("window_start") }}' or session_date > date '{{ var("snapshot_date") }}'
