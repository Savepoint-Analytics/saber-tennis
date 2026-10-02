{% if relation_exists('tennis', 'gold_match_features_asof') %}

select
    source_key,
    tour,
    match_id,
    tournament_id,
    match_date,
    player_a_id,
    player_b_id,
    count(*) as row_count
from tennis.gold_match_features_asof
group by
    source_key,
    tour,
    match_id,
    tournament_id,
    match_date,
    player_a_id,
    player_b_id
having count(*) > 1

union all

select
    source_key,
    tour,
    match_id,
    tournament_id,
    match_date,
    player_a_id,
    player_b_id,
    1 as row_count
from tennis.gold_match_features_asof
where player_a_id = player_b_id

{% else %}

select
    null::text as source_key,
    null::text as tour,
    null::text as match_id,
    null::text as tournament_id,
    null::date as match_date,
    null::text as player_a_id,
    null::text as player_b_id,
    null::integer as row_count
where false

{% endif %}
