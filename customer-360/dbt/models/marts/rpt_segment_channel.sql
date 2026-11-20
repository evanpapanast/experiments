-- Cells under the minimum group size are blanked, not dropped.
select segment, preferred_channel,
  {{ suppress('count(*)') }} as customers,
  {{ suppress('count(*)', 'round(sum(net_revenue))') }} as net_revenue,
  count(*) < {{ var('min_group_size') }} as suppressed
from {{ ref('int_customer_metrics') }}
group by 1, 2
