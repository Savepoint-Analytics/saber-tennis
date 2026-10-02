from datetime import date
from math import log
from pathlib import Path

import pandas as pd

from tennis_sabermetrics.evaluation.diagnostics import (
    _diagnostic_feature_cache_metadata,
    _event_level,
    _load_diagnostic_feature_cache,
    _write_diagnostic_feature_cache,
    build_calibration_rows,
    build_missingness_rows,
    build_prediction_diagnostics,
    build_segment_backtest_rows,
    build_source_composition_rows,
)
from tennis_sabermetrics.models.match_outcome import predict_match_baseline_probabilities


def test_prediction_diagnostics_builds_all_requested_outputs() -> None:
    frame = _feature_frame()

    result = build_prediction_diagnostics(frame, min_segment_size=2)

    assert result.calibration_rows
    assert result.missingness_rows
    assert result.segment_rows
    assert result.source_composition_rows
    assert result.event_mapping_rows
    assert result.unmapped_event_rows == 0
    assert {row.feature_name for row in result.missingness_rows} >= {
        "rank_log_diff",
        "serve_points_won_pct_diff",
    }


def test_calibration_missingness_and_segments_are_reusable() -> None:
    predictions = predict_match_baseline_probabilities(_feature_frame())

    calibration_rows = build_calibration_rows(predictions)
    missingness_rows = build_missingness_rows(predictions)
    segment_rows = build_segment_backtest_rows(predictions, min_segment_size=2)
    source_rows = build_source_composition_rows(predictions, min_segment_size=2)

    assert {row.model_name for row in calibration_rows} >= {"overall_elo", "logistic_baseline"}
    assert {row.stat_availability for row in missingness_rows} >= {"serve_and_return"}
    assert {row.ranking_coverage for row in segment_rows} >= {"both_ranked"}
    assert {row.source_key for row in source_rows} >= {"test"}
    assert {row.event_level for row in source_rows} >= {"tour_level", "challenger_level"}
    assert {row.draw_stage for row in source_rows} >= {"main_draw", "qualifying"}
    assert {row.ranking_population for row in source_rows} >= {"ranked_population"}
    assert {row.source_coverage for row in source_rows} >= {"other"}
    assert all(0.0 < row.source_share <= 1.0 for row in source_rows)


def test_event_level_mapping_uses_sackmann_tour_codes() -> None:
    source_key = "aneeshers_tennis_sackmann_archive"

    assert _event_level("G", tour="wta", source_key=source_key) == "grand_slam"
    assert _event_level("PM", tour="wta", source_key=source_key) == "tour_level"
    assert _event_level("T1", tour="wta", source_key=source_key) == "tour_level"
    assert _event_level("15", tour="wta", source_key=source_key) == "itf_level"
    assert _event_level("50+H", tour="wta", source_key=source_key) == "itf_level"
    assert _event_level("CC", tour="wta", source_key=source_key) == "itf_level"
    assert _event_level("25", tour="atp", source_key=source_key) == "itf_level"
    assert _event_level("S", tour="atp", source_key=source_key) == "itf_level"
    assert _event_level("C", tour="atp", source_key=source_key) == "challenger_level"
    assert _event_level("F", tour="atp", source_key=source_key) == "season_final"
    assert _event_level("D", tour="wta", source_key=source_key) == "team_cup"
    assert _event_level("O", tour="wta", source_key=source_key) == "olympics"


def test_diagnostic_feature_cache_requires_matching_metadata(tmp_path: Path) -> None:
    cache_path = tmp_path / "diagnostic_features.parquet"
    frame = pd.DataFrame(
        {
            "match_date": [date(2024, 1, 1)],
            "rank_log_diff": [0.25],
            "player_a_won": [True],
        }
    )
    metadata = _diagnostic_feature_cache_metadata(
        start_date=date(2024, 1, 1),
        end_date=None,
        limit=None,
        snapshot={
            "row_count": 1,
            "min_match_date": "2024-01-01",
            "max_match_date": "2024-01-01",
            "max_feature_asof_date": "2023-12-31",
        },
    )

    _write_diagnostic_feature_cache(frame, cache_path=cache_path, metadata=metadata)

    cached = _load_diagnostic_feature_cache(cache_path, expected_metadata=metadata)
    assert cached is not None
    assert cached.loc[0, "rank_log_diff"] == 0.25

    stale_metadata = {
        **metadata,
        "snapshot": {
            "row_count": 2,
            "min_match_date": "2024-01-01",
            "max_match_date": "2024-01-02",
            "max_feature_asof_date": "2024-01-01",
        },
    }
    assert _load_diagnostic_feature_cache(cache_path, expected_metadata=stale_metadata) is None


def _feature_frame() -> pd.DataFrame:
    rows = []
    for year in range(1990, 2024):
        for index in range(8):
            player_a_won = index % 2 == 0
            rows.append(_feature_row(year=year, index=index, player_a_won=player_a_won))
    return pd.DataFrame(rows)


def _feature_row(*, year: int, index: int, player_a_won: bool) -> dict[str, object]:
    match_date = date(year, 1, (index % 8) + 1)
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
        "surface": "Hard" if index % 3 else "Clay",
        "round": "Q1" if index % 5 == 0 else "R32",
        "best_of": 3 if index % 4 else 5,
        "tournament_level": "C" if index % 5 == 0 else "A",
        "draw_size": "32",
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
