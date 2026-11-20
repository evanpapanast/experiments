select region, preferred_channel, count(*) as customers
from {{ ref('int_customer_metrics') }}
where orders > 0
group by 1, 2
