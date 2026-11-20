{# Privacy test: every non-empty count in the column must be at least the minimum group size. #}
{% test min_group_size(model, column_name) %}
select {{ column_name }} from {{ model }}
where {{ column_name }} is not null and {{ column_name }} < {{ var('min_group_size') }}
{% endtest %}
