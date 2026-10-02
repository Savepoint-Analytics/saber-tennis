{% if relation_exists('tennis', 'gold_match_features_asof') %}

select *
from tennis.gold_match_features_asof
where not (
    (((player_a_rank is null or player_b_rank is null) and rank_diff is null)
        or (player_a_rank is not null and player_b_rank is not null and rank_diff = player_b_rank - player_a_rank))
    and (((player_a_rank is null or player_b_rank is null) and rank_log_diff is null)
        or (
            player_a_rank is not null
            and player_b_rank is not null
            and rank_log_diff is not null
            and abs(rank_log_diff - ln((player_b_rank + 1.0) / (player_a_rank + 1.0))) < 0.000001
        ))
    and abs(overall_elo_diff - (player_a_overall_elo - player_b_overall_elo)) < 0.000001
    and abs(surface_elo_diff - (player_a_surface_elo - player_b_surface_elo)) < 0.000001
    and (((player_a_prior_win_pct is null or player_b_prior_win_pct is null) and prior_win_pct_diff is null)
        or (
            player_a_prior_win_pct is not null
            and player_b_prior_win_pct is not null
            and prior_win_pct_diff is not null
            and abs(prior_win_pct_diff - (player_a_prior_win_pct - player_b_prior_win_pct)) < 0.000001
        ))
    and (((player_a_recent_10_win_pct is null or player_b_recent_10_win_pct is null) and recent_10_win_pct_diff is null)
        or (
            player_a_recent_10_win_pct is not null
            and player_b_recent_10_win_pct is not null
            and recent_10_win_pct_diff is not null
            and abs(recent_10_win_pct_diff - (player_a_recent_10_win_pct - player_b_recent_10_win_pct)) < 0.000001
        ))
    and (((player_a_days_since_last_match is null or player_b_days_since_last_match is null) and rest_days_diff is null)
        or (
            player_a_days_since_last_match is not null
            and player_b_days_since_last_match is not null
            and rest_days_diff = player_a_days_since_last_match - player_b_days_since_last_match
        ))
    and (((player_a_serve_points_won_pct_prior is null or player_b_serve_points_won_pct_prior is null) and serve_points_won_pct_diff is null)
        or (
            player_a_serve_points_won_pct_prior is not null
            and player_b_serve_points_won_pct_prior is not null
            and serve_points_won_pct_diff is not null
            and abs(serve_points_won_pct_diff - (player_a_serve_points_won_pct_prior - player_b_serve_points_won_pct_prior)) < 0.000001
        ))
    and (((player_a_return_points_won_pct_prior is null or player_b_return_points_won_pct_prior is null) and return_points_won_pct_diff is null)
        or (
            player_a_return_points_won_pct_prior is not null
            and player_b_return_points_won_pct_prior is not null
            and return_points_won_pct_diff is not null
            and abs(return_points_won_pct_diff - (player_a_return_points_won_pct_prior - player_b_return_points_won_pct_prior)) < 0.000001
        ))
)

{% else %}

select 1 as missing_gold_table
where false

{% endif %}
