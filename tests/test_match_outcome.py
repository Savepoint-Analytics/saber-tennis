from datetime import date
from math import log

import pandas as pd
import pytest

from tennis_sabermetrics.evaluation.leakage_checks import FeatureLeakageError
from tennis_sabermetrics.models.match_outcome import (
    default_temporal_split,
    evaluate_match_baselines,
    ranking_baseline_probability,
)


def test_ranking_baseline_probability_increases_with_better_player_a_rank() -> None:
    probabilities = ranking_baseline_probability(pd.Series([1.0, 0.0, -1.0]))

    assert probabilities[0] > probabilities[1] > probabilities[2]


def test_evaluate_match_baselines_returns_validation_and_test_metrics() -> None:
    rows = []
    for year in range(1990, 2024):
        for index in range(6):
            stronger_a = index % 2 == 0
            rows.append(_feature_row(year=year, index=index, player_a_won=stronger_a))
            rows.append(
                _feature_row(year=year, index=index + 100, player_a_won=not stronger_a)
            )

    results = evaluate_match_baselines(pd.DataFrame(rows), split=default_temporal_split())
    keys = {(row.model_name, row.split) for row in results}

    assert ("ranking_log_difference", "validation") in keys
    assert ("overall_elo", "test") in keys
    assert ("surface_elo", "test") in keys
    assert ("logistic_baseline", "validation") in keys
    assert ("overall_elo_platt", "test") in keys
    assert ("logistic_baseline_platt", "test") in keys
    assert ("overall_elo_isotonic", "test") in keys
    assert ("logistic_baseline_isotonic", "test") in keys
    assert ("logistic_baseline_platt", "validation") not in keys
    assert ("logistic_baseline_isotonic", "validation") not in keys
    assert all(row.sample_size > 0 for row in results)


def test_evaluate_match_baselines_rejects_future_ranking_feature() -> None:
    rows = [
        _feature_row(year=2018, index=1, player_a_won=True),
        _feature_row(year=2019, index=1, player_a_won=False),
        _feature_row(year=2022, index=1, player_a_won=True),
    ]
    rows[0]["player_a_rank_asof_date"] = date(2018, 1, 2)
    rows[0]["max_feature_asof_date"] = date(2018, 1, 2)

    with pytest.raises(FeatureLeakageError):
        evaluate_match_baselines(pd.DataFrame(rows), split=default_temporal_split())


def test_evaluate_match_baselines_rejects_duplicate_feature_join_rows() -> None:
    row = _feature_row(year=2018, index=1, player_a_won=True)

    with pytest.raises(FeatureLeakageError):
        evaluate_match_baselines(pd.DataFrame([row, row]), split=default_temporal_split())


def _feature_row(*, year: int, index: int, player_a_won: bool) -> dict[str, object]:
    match_date = date(year, 1, (index % 6) + 1)
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
        "match_date": match_date,
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
