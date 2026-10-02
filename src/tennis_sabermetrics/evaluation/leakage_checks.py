"""Leakage guardrails used by feature builders and model evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from tennis_sabermetrics.config import PostgresSettings


def assert_feature_asof_date(feature_asof_date: date, match_date: date) -> None:
    if feature_asof_date >= match_date:
        raise ValueError(
            f"Feature as-of date {feature_asof_date.isoformat()} must be before "
            f"match date {match_date.isoformat()}"
        )


@dataclass(frozen=True)
class LeakageCheckResult:
    check_name: str
    violation_count: int
    details: str

    @property
    def passed(self) -> bool:
        return self.violation_count == 0


class FeatureLeakageError(ValueError):
    """Raised when a feature table is unsafe for pre-match model evaluation."""


FEATURE_LEAKAGE_COLUMNS = (
    "feature_row_id",
    "source_key",
    "tour",
    "match_id",
    "tournament_id",
    "match_date",
    "player_a_id",
    "player_b_id",
    "player_a_rank",
    "player_b_rank",
    "player_a_rank_asof_date",
    "player_b_rank_asof_date",
    "rank_diff",
    "rank_log_diff",
    "player_a_overall_elo",
    "player_b_overall_elo",
    "overall_elo_diff",
    "player_a_surface_elo",
    "player_b_surface_elo",
    "surface_elo_diff",
    "player_a_prior_matches",
    "player_b_prior_matches",
    "player_a_prior_win_pct",
    "player_b_prior_win_pct",
    "prior_win_pct_diff",
    "player_a_recent_10_win_pct",
    "player_b_recent_10_win_pct",
    "recent_10_win_pct_diff",
    "player_a_days_since_last_match",
    "player_b_days_since_last_match",
    "rest_days_diff",
    "player_a_serve_points_won_pct_prior",
    "player_b_serve_points_won_pct_prior",
    "serve_points_won_pct_diff",
    "player_a_return_points_won_pct_prior",
    "player_b_return_points_won_pct_prior",
    "return_points_won_pct_diff",
    "max_feature_asof_date",
)


def validate_feature_frame_before_evaluation(frame: pd.DataFrame) -> list[LeakageCheckResult]:
    """Return leakage and feature-join validation results for a model input frame."""

    missing = [column for column in FEATURE_LEAKAGE_COLUMNS if column not in frame.columns]
    if missing:
        return [
            LeakageCheckResult(
                "required_leakage_columns_present",
                len(missing),
                f"Missing required columns: {', '.join(missing)}",
            )
        ]

    working = frame.copy()
    working["match_date"] = pd.to_datetime(working["match_date"]).dt.date
    for column in (
        "player_a_rank_asof_date",
        "player_b_rank_asof_date",
        "max_feature_asof_date",
    ):
        working[column] = pd.to_datetime(working[column]).dt.date

    natural_key = [
        "source_key",
        "tour",
        "match_id",
        "tournament_id",
        "match_date",
        "player_a_id",
        "player_b_id",
    ]
    results = [
        LeakageCheckResult(
            "feature_row_id_unique",
            int(working["feature_row_id"].duplicated().sum()),
            "Each gold feature row must have a unique feature_row_id.",
        ),
        LeakageCheckResult(
            "natural_match_feature_grain_unique",
            int(working.duplicated(subset=natural_key).sum()),
            "Feature joins must produce one row per oriented match grain.",
        ),
        LeakageCheckResult(
            "players_are_distinct",
            int((working["player_a_id"] == working["player_b_id"]).sum()),
            "A match feature row cannot compare a player with themselves.",
        ),
        LeakageCheckResult(
            "max_feature_asof_before_match",
            _count_date_not_before(working, "max_feature_asof_date", "match_date"),
            "All joined features must be known before match_date.",
        ),
        LeakageCheckResult(
            "player_a_rank_asof_before_match",
            _count_date_not_before(working, "player_a_rank_asof_date", "match_date"),
            "Player A ranking features must use rankings before match_date.",
        ),
        LeakageCheckResult(
            "player_b_rank_asof_before_match",
            _count_date_not_before(working, "player_b_rank_asof_date", "match_date"),
            "Player B ranking features must use rankings before match_date.",
        ),
        LeakageCheckResult(
            "rank_and_rank_asof_nulls_match",
            _count_null_mismatch(working, "player_a_rank", "player_a_rank_asof_date")
            + _count_null_mismatch(working, "player_b_rank", "player_b_rank_asof_date"),
            "Rank values and rank as-of dates must be present or absent together.",
        ),
        LeakageCheckResult(
            "rest_days_non_negative",
            int(
                (working["player_a_days_since_last_match"].dropna() < 0).sum()
                + (working["player_b_days_since_last_match"].dropna() < 0).sum()
            ),
            "Prior-match rest features cannot refer to matches after match_date.",
        ),
        LeakageCheckResult(
            "difference_columns_consistent",
            _count_difference_violations(working),
            "Difference features must equal player A value minus player B value.",
        ),
        LeakageCheckResult(
            "rank_log_diff_consistent",
            _count_rank_log_violations(working),
            "rank_log_diff must equal log((player_b_rank + 1) / (player_a_rank + 1)).",
        ),
    ]
    return results


def assert_feature_frame_safe_for_evaluation(frame: pd.DataFrame) -> None:
    results = validate_feature_frame_before_evaluation(frame)
    failures = [result for result in results if not result.passed]
    if failures:
        detail = "; ".join(
            f"{failure.check_name}={failure.violation_count}" for failure in failures
        )
        raise FeatureLeakageError(f"Feature table failed leakage checks: {detail}")


def assert_postgres_feature_table_safe_for_evaluation(
    *,
    conninfo: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[LeakageCheckResult]:
    """Run leakage checks in PostgreSQL before loading features for model evaluation."""

    import psycopg

    where_sql, params = _date_filter_sql(start_date, end_date)
    results: list[LeakageCheckResult] = []
    with psycopg.connect(conninfo or PostgresSettings.from_env().conninfo) as connection:
        with connection.cursor() as cursor:
            for check_name, sql, details in _postgres_leakage_queries(where_sql):
                cursor.execute(sql, params)
                row = cursor.fetchone()
                if row is None:
                    raise FeatureLeakageError(f"Leakage check returned no result: {check_name}")
                violation_count = int(row[0])
                results.append(LeakageCheckResult(check_name, violation_count, details))

    failures = [result for result in results if not result.passed]
    if failures:
        detail = "; ".join(
            f"{failure.check_name}={failure.violation_count}" for failure in failures
        )
        raise FeatureLeakageError(f"Feature table failed PostgreSQL leakage checks: {detail}")
    return results


def _date_filter_sql(start_date: date | None, end_date: date | None) -> tuple[str, tuple[date, ...]]:
    conditions = ["1 = 1"]
    params: list[date] = []
    if start_date is not None:
        conditions.append("match_date >= %s")
        params.append(start_date)
    if end_date is not None:
        conditions.append("match_date <= %s")
        params.append(end_date)
    return " and ".join(conditions), tuple(params)


def _postgres_leakage_queries(where_sql: str) -> tuple[tuple[str, str, str], ...]:
    table_sql = f"(select * from tennis.gold_match_features_asof where {where_sql}) checked"
    return (
        (
            "feature_row_id_unique",
            f"""
            select count(*)
            from (
                select feature_row_id
                from {table_sql}
                group by feature_row_id
                having count(*) > 1
            ) duplicated
            """,
            "Each gold feature row must have a unique feature_row_id.",
        ),
        (
            "natural_match_feature_grain_unique",
            f"""
            select count(*)
            from (
                select
                    source_key, tour, match_id, tournament_id, match_date, player_a_id, player_b_id
                from {table_sql}
                group by source_key, tour, match_id, tournament_id, match_date, player_a_id, player_b_id
                having count(*) > 1
            ) duplicated
            """,
            "Feature joins must produce one row per oriented match grain.",
        ),
        (
            "players_are_distinct",
            f"select count(*) from {table_sql} where player_a_id = player_b_id",
            "A match feature row cannot compare a player with themselves.",
        ),
        (
            "max_feature_asof_before_match",
            f"""
            select count(*)
            from {table_sql}
            where max_feature_asof_date is not null
              and max_feature_asof_date >= match_date
            """,
            "All joined features must be known before match_date.",
        ),
        (
            "ranking_asof_before_match",
            f"""
            select count(*)
            from {table_sql}
            where (player_a_rank_asof_date is not null and player_a_rank_asof_date >= match_date)
               or (player_b_rank_asof_date is not null and player_b_rank_asof_date >= match_date)
            """,
            "Ranking features must use rankings before match_date.",
        ),
        (
            "rank_and_rank_asof_nulls_match",
            f"""
            select count(*)
            from {table_sql}
            where (player_a_rank is null) <> (player_a_rank_asof_date is null)
               or (player_b_rank is null) <> (player_b_rank_asof_date is null)
            """,
            "Rank values and rank as-of dates must be present or absent together.",
        ),
        (
            "rest_days_non_negative",
            f"""
            select count(*)
            from {table_sql}
            where player_a_days_since_last_match < 0
               or player_b_days_since_last_match < 0
            """,
            "Prior-match rest features cannot refer to matches after match_date.",
        ),
        (
            "difference_columns_consistent",
            f"""
            select count(*)
            from {table_sql}
            where not (
                { _diff_sql("player_a_rank", "player_b_rank", "rank_diff", "integer", invert=True) }
                and { _diff_sql("player_a_overall_elo", "player_b_overall_elo", "overall_elo_diff", "double precision") }
                and { _diff_sql("player_a_surface_elo", "player_b_surface_elo", "surface_elo_diff", "double precision") }
                and { _diff_sql("player_a_prior_win_pct", "player_b_prior_win_pct", "prior_win_pct_diff", "double precision") }
                and { _diff_sql("player_a_recent_10_win_pct", "player_b_recent_10_win_pct", "recent_10_win_pct_diff", "double precision") }
                and { _diff_sql("player_a_days_since_last_match", "player_b_days_since_last_match", "rest_days_diff", "integer") }
                and { _diff_sql("player_a_serve_points_won_pct_prior", "player_b_serve_points_won_pct_prior", "serve_points_won_pct_diff", "double precision") }
                and { _diff_sql("player_a_return_points_won_pct_prior", "player_b_return_points_won_pct_prior", "return_points_won_pct_diff", "double precision") }
            )
            """,
            "Difference features must match their player A and player B inputs.",
        ),
        (
            "rank_log_diff_consistent",
            f"""
            select count(*)
            from {table_sql}
            where not (
                ((player_a_rank is null or player_b_rank is null) and rank_log_diff is null)
                or (
                    player_a_rank is not null
                    and player_b_rank is not null
                    and rank_log_diff is not null
                    and abs(rank_log_diff - ln((player_b_rank + 1.0) / (player_a_rank + 1.0))) < 0.000001
                )
            )
            """,
            "rank_log_diff must match the joined rank values.",
        ),
    )


def _diff_sql(
    left_column: str,
    right_column: str,
    diff_column: str,
    data_type: str,
    *,
    invert: bool = False,
) -> str:
    expression = (
        f"{right_column} - {left_column}" if invert else f"{left_column} - {right_column}"
    )
    return f"""
    (
        ({left_column} is null or {right_column} is null) and {diff_column} is null
    )
    or (
        {left_column} is not null
        and {right_column} is not null
        and {diff_column} is not null
        and abs(({diff_column})::{data_type} - ({expression})::{data_type}) < 0.000001
    )
    """


def _count_date_not_before(frame: pd.DataFrame, feature_date_column: str, match_date_column: str) -> int:
    feature_dates = frame[feature_date_column]
    mask = feature_dates.notna() & (feature_dates >= frame[match_date_column])
    return int(mask.sum())


def _count_null_mismatch(frame: pd.DataFrame, left_column: str, right_column: str) -> int:
    return int((frame[left_column].isna() != frame[right_column].isna()).sum())


def _count_difference_violations(frame: pd.DataFrame) -> int:
    checks = (
        ("player_a_rank", "player_b_rank", "rank_diff", True),
        ("player_a_overall_elo", "player_b_overall_elo", "overall_elo_diff", False),
        ("player_a_surface_elo", "player_b_surface_elo", "surface_elo_diff", False),
        ("player_a_prior_win_pct", "player_b_prior_win_pct", "prior_win_pct_diff", False),
        (
            "player_a_recent_10_win_pct",
            "player_b_recent_10_win_pct",
            "recent_10_win_pct_diff",
            False,
        ),
        ("player_a_days_since_last_match", "player_b_days_since_last_match", "rest_days_diff", False),
        (
            "player_a_serve_points_won_pct_prior",
            "player_b_serve_points_won_pct_prior",
            "serve_points_won_pct_diff",
            False,
        ),
        (
            "player_a_return_points_won_pct_prior",
            "player_b_return_points_won_pct_prior",
            "return_points_won_pct_diff",
            False,
        ),
    )
    violations = 0
    for left_column, right_column, diff_column, invert in checks:
        violations += _count_difference_mismatch(
            frame, left_column, right_column, diff_column, invert=invert
        )
    return violations


def _count_rank_log_violations(frame: pd.DataFrame) -> int:
    left = frame["player_a_rank"]
    right = frame["player_b_rank"]
    rank_log_diff = frame["rank_log_diff"]
    both_present = left.notna() & right.notna()
    expected = np.log((right.astype(float) + 1.0) / (left.astype(float) + 1.0))
    null_mismatch = int((both_present & rank_log_diff.isna()).sum())
    unexpected_value = int((~both_present & rank_log_diff.notna()).sum())
    value_mismatch = int(
        (
            both_present
            & rank_log_diff.notna()
            & ((rank_log_diff.astype(float) - expected).abs() > 1e-6)
        ).sum()
    )
    return null_mismatch + unexpected_value + value_mismatch


def _count_difference_mismatch(
    frame: pd.DataFrame,
    left_column: str,
    right_column: str,
    diff_column: str,
    *,
    invert: bool = False,
) -> int:
    left = frame[left_column]
    right = frame[right_column]
    diff = frame[diff_column]
    both_present = left.notna() & right.notna()
    expected = right - left if invert else left - right
    null_mismatch = int((both_present & diff.isna()).sum())
    unexpected_value = int((~both_present & diff.notna()).sum())
    value_mismatch = int(
        (both_present & diff.notna() & ((diff.astype(float) - expected.astype(float)).abs() > 1e-6)).sum()
    )
    return null_mismatch + unexpected_value + value_mismatch
