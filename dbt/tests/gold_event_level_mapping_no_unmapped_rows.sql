{% if relation_exists('tennis', 'gold_event_level_mapping_diagnostics') %}

select *
from tennis.gold_event_level_mapping_diagnostics
where not is_mapped

{% else %}

select 1 as missing_event_mapping_diagnostics
where false

{% endif %}
