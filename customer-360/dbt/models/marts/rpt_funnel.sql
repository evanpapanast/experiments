select channel, count(*) as sessions, countif(reached_product) as product, countif(reached_cart) as cart,
  countif(purchased) as purchase, countif(customer_id is null) as anonymous_sessions
from {{ ref('stg_sessions') }}
group by 1
