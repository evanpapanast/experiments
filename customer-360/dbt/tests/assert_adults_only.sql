-- Privacy: the customer table holds exactly the adults of the source, and nobody else.
select * from (
  select (select count(*) from {{ ref('stg_customers') }}) as model_count,
         (select count(*) from {{ source('thelook', 'users') }}
          where age >= {{ var('min_age') }} and date(created_at) <= date '{{ var("snapshot_date") }}') as source_adults
) where model_count != source_adults
