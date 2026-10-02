from datetime import date
from math import log

import pandas as pd

from tennis_sabermetrics.evaluation.walk_forward import (
    default_walk_forward_splits,
    evaluate_walk_forward_baselines,
)


def test_default_walk_forward_splits_are_ordered() -> None:
    splits = default_walk_forward_splits(
        first_test_year=2019,
        last_test_year=2020,
        validation_years=2,
    )

    assert len(splits) == 2
    assert splits[0].train_end == date(2016, 12, 31)
    assert splits[0].validation_start == date(2017, 1, 1)
    assert splits[0].test_start == date(2019, 1, 1)
    assert splits[1].test_end == date(2020, 12, 31)


def test_evaluate_walk_forward_baselines_returns_test_rows_only() -> None:
    frame = pd.DataFrame(
        [
            _feature_row(year=year, index=index, player_a_won=index % 2 == 0)
            for year in range(1990, 2021)
            for index in range(6)
        ]
    )
    splits = default_walk_forward_splits(
        first_test_year=2019,
        last_test_year=2020,
        validation_years=2,
    )

    rows = evaluate_walk_forward_baselines(frame, splits=splits)

    assert {row.window_label for row in rows} == {"2019", "2020"}
    assert {row.split for row in rows} == {"test"}
    assert {row.model_name for row in rows} >= {
        "overall_elo",
        "logistic_baseline_platt",
        "logistic_baseline_isotonic",
    }
    assert all(row.sample_size > 0 for row in rows)


def test_evaluate_walk_forward_baselines_can_use_narrow_safe_frame() -> None:
    frame = pd.DataFrame(
        [
            _feature_row(year=year, index=index, player_a_won=index % 2 == 0)
            for year in range(1990, 2021)
            for index in range(6)
        ]
    ).loc[
        :,
        [
            "match_date",
            "player_a_won",
            "rank_log_diff",
            "overall_elo_diff",
            "surface_elo_diff",
            "prior_win_pct_diff",
            "recent_10_win_pct_diff",
            "rest_days_diff",
            "serve_points_won_pct_diff",
            "return_points_won_pct_diff",
        ],
    ]
    splits = default_walk_forward_splits(
        first_test_year=2019,
        last_test_year=2019,
        validation_years=2,
    )

    rows = evaluate_walk_forward_baselines(frame, splits=splits, assume_safe=True)

    assert len(rows) == 12
    assert {row.model_name for row in rows} >= {
        "ranking_log_difference",
        "logistic_baseline_isotonic",
    }


def _feature_row(*, year: int, index: int, player_a_won: bool) -> dict[str, object]:
    player_a_rank = 10 if player_a_won else 40
    player_b_rank = 40 if player_a_won else 10
    player_a_overall_elo = 1600.0 if player_a_won else 1400.0
    player_b_overall_elo = 1400.0 if player_a_won else 1600.0
    player_a_surface_elo = 1580.0 if player_a_won else 1420.0
    player_b_surface_elo = 1420.0 if player_a_won else 1580.0
    player_a_prior_win_pct = 0.6 if player_a_won else 0.4
    player_b_prior_win_pct = 0.4 if player_a_won else 0.6
    player_a_recent = 0.7 if player_a_won else 0.3
    player_b_recent = 0.3 if player_a_won else 0.7
    player_a_rest = 6 if player_a_won else 3
    player_b_rest = 3 if player_a_won else 6
    player_a_serve = 0.66 if player_a_won else 0.61
    player_b_serve = 0.61 if player_a_won else 0.66
    player_a_return = 0.39 if player_a_won else 0.36
    player_b_return = 0.36 if player_a_won else 0.39
    return {
        "feature_row_id": f"feature-{year}-{index}",
        "source_key": "test",
        "tour": "atp",
        "match_id": f"match-{year}-{index}",
        "tournament_id": f"tournament-{year}",
        "match_date": date(year, 1, (index % 6) + 1),
        "surface": "Hard",
        "round": "R32",
        "best_of": 3,
        "player_a_id": f"A-{index}",
        "player_b_id": f"B-{index}",
        "player_a_won": player_a_won,
        "player_a_rank": player_a_rank,
        "player_b_rank": player_b_rank,
        "player_a_rank_asof_date": date(year - 1, 12, 31),
        "player_b_rank_asof_date": date(year - 1, 12, 31),
        "rank_diff": player_b_rank - player_a_rank,
        "rank_log_diff": log((player_b_rank + 1) / (player_a_rank + 1)),
        "player_a_overall_elo": player_a_overall_elo,
        "player_b_overall_elo": player_b_overall_elo,
        "overall_elo_diff": player_a_overall_elo - player_b_overall_elo,
        "player_a_surface_elo": player_a_surface_elo,
        "player_b_surface_elo": player_b_surface_elo,
        "surface_elo_diff": player_a_surface_elo - player_b_surface_elo,
        "player_a_prior_matches": 25,
        "player_b_prior_matches": 25,
        "player_a_prior_win_pct": player_a_prior_win_pct,
        "player_b_prior_win_pct": player_b_prior_win_pct,
        "prior_win_pct_diff": player_a_prior_win_pct - player_b_prior_win_pct,
        "player_a_recent_10_win_pct": player_a_recent,
        "player_b_recent_10_win_pct": player_b_recent,
        "recent_10_win_pct_diff": player_a_recent - player_b_recent,
        "player_a_days_since_last_match": player_a_rest,
        "player_b_days_since_last_match": player_b_rest,
        "rest_days_diff": player_a_rest - player_b_rest,
        "player_a_serve_points_won_pct_prior": player_a_serve,
        "player_b_serve_points_won_pct_prior": player_b_serve,
        "serve_points_won_pct_diff": player_a_serve - player_b_serve,
        "player_a_return_points_won_pct_prior": player_a_return,
        "player_b_return_points_won_pct_prior": player_b_return,
        "return_points_won_pct_diff": player_a_return - player_b_return,
        "max_feature_asof_date": date(year - 1, 12, 31),
    }
