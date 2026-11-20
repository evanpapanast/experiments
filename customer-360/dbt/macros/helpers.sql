{# Revenue rules used everywhere: net = not cancelled and not returned. #}
{% macro is_net(status='status') -%}
  {{ status }} not in ('Cancelled', 'Returned')
{%- endmacro %}

{% macro is_shipped(status='status') -%}
  {{ status }} != 'Cancelled'
{%- endmacro %}

{# Map the source's channel names to report names. #}
{% macro channel_name(col) -%}
  case {{ col }} when 'Adwords' then 'Google Ads' else {{ col }} end
{%- endmacro %}

{# Privacy: blank out any count (and its revenue) below the minimum group size. #}
{% macro suppress(count_expr, value_expr=none) -%}
  {%- if value_expr is none -%}
  if({{ count_expr }} < {{ var('min_group_size') }}, null, {{ count_expr }})
  {%- else -%}
  if({{ count_expr }} < {{ var('min_group_size') }}, null, {{ value_expr }})
  {%- endif -%}
{%- endmacro %}

{% macro window_filter(ts_col) -%}
  {{ ts_col }} >= timestamp('{{ var("window_start") }}') and {{ ts_col }} < timestamp('{{ var("window_end_exclusive") }}')
{%- endmacro %}
