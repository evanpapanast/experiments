-- Customers: ID plus coarse attributes only. Adults only. Country is replaced by four regions.
select
  id as customer_id,
  case when age < 25 then '18-24' when age < 35 then '25-34' when age < 45 then '35-44'
       when age < 55 then '45-54' else '55-70' end as age_band,
  if(gender = 'M', 'Men', 'Women') as gender,
  case
    when country in ('China', 'South Korea', 'Japan', 'Australia') then 'Asia-Pacific'
    when country = 'United States' then 'North America'
    when country in ('Brasil', 'Colombia') then 'Latin America'
    else 'Europe' end as region,
  traffic_source as acquisition_channel,
  date_trunc(date(created_at), month) as signup_month
from {{ source('thelook', 'users') }}
where age >= {{ var('min_age') }}
  and date(created_at) <= date '{{ var("snapshot_date") }}'
