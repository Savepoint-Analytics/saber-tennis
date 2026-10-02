{% if relation_exists('tennis', 'gold_match_features_asof') %}

with event_codes as (
    select
        source_key,
        tour,
        tournament_level,
        count(*) as row_count
    from tennis.gold_match_features_asof
    group by 1, 2, 3
),

mapped as (
    select
        *,
        case
            when tournament_level is null then 'unknown'
            when upper(trim(tournament_level::text)) = 'G' then 'grand_slam'
            when upper(trim(tournament_level::text)) = 'D' then 'team_cup'
            when upper(trim(tournament_level::text)) = 'O' then 'olympics'
            when upper(trim(tournament_level::text)) = 'E' then 'exhibition'
            when upper(trim(tournament_level::text)) = 'J' then 'junior'
            when upper(trim(tournament_level::text)) = 'T' then 'team_tennis'
            when upper(trim(tournament_level::text)) = 'F' then 'season_final'
            when upper(trim(tournament_level::text)) in ('M', 'A', 'P', 'PM', 'P5', 'I', 'W')
                or upper(trim(tournament_level::text)) like 'T%'
                then 'tour_level'
            when upper(trim(tournament_level::text)) = 'C' then 'challenger_level'
            when upper(trim(tournament_level::text)) = 'CC'
                and lower(trim(tour::text)) = 'wta'
                and (
                    lower(trim(source_key::text)) like 'jeffsackmann_%'
                    or lower(trim(source_key::text)) = 'aneeshers_tennis_sackmann_archive'
                )
                then 'itf_level'
            when upper(trim(tournament_level::text)) = 'S'
                and lower(trim(tour::text)) = 'atp'
                and (
                    lower(trim(source_key::text)) like 'jeffsackmann_%'
                    or lower(trim(source_key::text)) = 'aneeshers_tennis_sackmann_archive'
                )
                then 'itf_level'
            when (
                    lower(trim(source_key::text)) like 'jeffsackmann_%'
                    or lower(trim(source_key::text)) = 'aneeshers_tennis_sackmann_archive'
                )
                and regexp_replace(upper(trim(tournament_level::text)), '\+H$', '') ~ '^[0-9]+$'
                then 'itf_level'
            else 'unknown'
        end as event_level
    from event_codes
)

select *
from mapped
where event_level = 'unknown'

{% else %}

select 1 as missing_gold_table
where false

{% endif %}
