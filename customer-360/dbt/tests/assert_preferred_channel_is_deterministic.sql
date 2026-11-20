-- Reproducibility: recompute the preferred channel with the same strict ordering and compare.
-- Fails if any customer would get a different channel, e.g. if the tie-break in int_customer_metrics is removed.
with s as (
  select customer_id, channel, count(*) as n, max(session_start) as last_ts
  from {{ ref('stg_sessions') }} where customer_id is not null group by 1, 2
),
ranked as (
  select customer_id, channel,
    row_number() over (partition by customer_id order by n desc, last_ts desc, channel) as rk
  from s
)
select m.customer_id
from {{ ref('int_customer_metrics') }} m
join ranked r on r.customer_id = m.customer_id and r.rk = 1
where m.preferred_channel != r.channel
