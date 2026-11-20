{% set dims = [('region', 'region'), ('age_band', 'age_band'), ('gender', 'gender')] %}
{% for label, col in dims %}
select '{{ label }}' as dim, {{ col }} as val, count(*) as customers, countif(orders > 0) as buyers,
  round(sum(net_revenue)) as net_revenue, round(sum(net_revenue - net_cost)) as gross_margin,
  round(sum(returned_value)) as returned_value, round(sum(gross_sales)) as gross_sales
from {{ ref('int_customer_metrics') }}
group by 1, 2
{% if not loop.last %}union all{% endif %}
{% endfor %}
