-- Privacy: no personal-data column may exist anywhere in the dbt dataset.
select table_name, column_name
from `{{ target.project }}.{{ target.dataset }}`.INFORMATION_SCHEMA.COLUMNS
where lower(column_name) in ('first_name', 'last_name', 'email', 'street_address', 'postal_code', 'city', 'state',
                             'latitude', 'longitude', 'ip_address', 'browser', 'uri', 'age', 'user_geom', 'country')
