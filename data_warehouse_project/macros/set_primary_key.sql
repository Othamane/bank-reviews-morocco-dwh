-- macros/set_primary_key.sql
{% macro set_primary_key(table_name, pk_column) %}
  ALTER TABLE {{ table_name }}
  ADD PRIMARY KEY ({{ pk_column }});
{% endmacro %}
