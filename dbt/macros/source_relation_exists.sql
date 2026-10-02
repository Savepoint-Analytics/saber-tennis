{% macro source_relation_exists(source_name, table_name) -%}
    {%- set source_relation = source(source_name, table_name) -%}
    {%- set relation = adapter.get_relation(
        database=source_relation.database,
        schema=source_relation.schema,
        identifier=source_relation.identifier
    ) -%}
    {{ return(relation is not none) }}
{%- endmacro %}
