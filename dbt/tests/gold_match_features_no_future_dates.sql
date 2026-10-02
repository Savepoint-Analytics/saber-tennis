{% if relation_exists('tennis', 'gold_match_features_asof') %}

select *
from tennis.gold_match_features_asof
where (max_feature_asof_date is not null and max_feature_asof_date >= match_date)
   or (player_a_rank_asof_date is not null and player_a_rank_asof_date >= match_date)
   or (player_b_rank_asof_date is not null and player_b_rank_asof_date >= match_date)

{% else %}

select 1 as missing_gold_table
where false

{% endif %}
