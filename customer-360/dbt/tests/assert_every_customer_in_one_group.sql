-- Completeness: group sizes add up to all customers.
select * from (
  select (select sum(customers) from {{ ref('rpt_segments') }}) as in_groups,
         (select count(*) from {{ ref('stg_customers') }}) as customers
) where in_groups != customers
