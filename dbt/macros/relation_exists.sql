{% macro relation_exists(schema_name, table_name) -%}
    {%- set relation = adapter.get_relation(
        database=target.database,
        schema=schema_name,
        identifier=table_name
    ) -%}
    {{ return(relation is not none) }}
{%- endmacro %}
