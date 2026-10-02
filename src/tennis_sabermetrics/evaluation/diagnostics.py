"""Calibration, missingness, and segmented backtest diagnostics."""

from __future__ import annotations

import csv
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import plotly.graph_objects as go  # type: ignore[import-untyped]

from tennis_sabermetrics.config import PostgresSettings
from tennis_sabermetrics.evaluation.leakage_checks import (
    assert_postgres_feature_table_safe_for_evaluation,
)
from tennis_sabermetrics.evaluation.metrics import evaluate_binary_probabilities
from tennis_sabermetrics.models.match_outcome import (
    BASELINE_PROBABILITY_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    default_temporal_split,
    evaluation_splits_for_model,
    predict_match_baseline_probabilities,
)


@dataclass(frozen=True)
class CalibrationRow:
    model_name: str
    split: str
    probability_bin: int
    bin_lower: float
    bin_upper: float
    sample_size: int
    mean_predicted_probability: float
    observed_win_rate: float
    calibration_error: float


@dataclass(frozen=True)
class MissingnessRow:
    tour: str
    surface: str
    era: str
    stat_availability: str
    feature_name: str
    row_count: int
    available_count: int
    missing_count: int
    missing_rate: float


@dataclass(frozen=True)
class SegmentBacktestRow:
    model_name: str
    split: str
    tour: str
    surface: str
    match_format: str
    event_level: str
    draw_stage: str
    era: str
    ranking_coverage: str
    ranking_population: str
    source_coverage: str
    log_loss: float
    brier_score: float
    roc_auc: float | None
    accuracy: float
    sample_size: int


@dataclass(frozen=True)
class SourceCompositionRow:
    split: str
    tour: str
    surface: str
    match_format: str
    event_level: str
    draw_stage: str
    era: str
    ranking_coverage: str
    ranking_population: str
    source_coverage: str
    source_key: str
    segment_sample_size: int
    source_sample_size: int
    source_share: float
    match_start: date
    match_end: date
    serve_return_available_rate: float
    both_ranked_rate: float
    logistic_log_loss: float | None
    logistic_roc_auc: float | None


@dataclass(frozen=True)
class EventLevelMappingRow:
    source_key: str
    tour: str
    tournament_level: str
    event_level: str
    row_count: int
    is_mapped: bool


@dataclass(frozen=True)
class DiagnosticBuildResult:
    calibration_rows: list[CalibrationRow]
    missingness_rows: list[MissingnessRow]
    segment_rows: list[SegmentBacktestRow]
    source_composition_rows: list[SourceCompositionRow]
    event_mapping_rows: list[EventLevelMappingRow]
    calibration_plot_path: Path | None

    @property
    def unmapped_event_rows(self) -> int:
        return sum(row.row_count for row in self.event_mapping_rows if not row.is_mapped)


CALIBRATION_COLUMNS = tuple(CalibrationRow.__dataclass_fields__)
MISSINGNESS_COLUMNS = tuple(MissingnessRow.__dataclass_fields__)
SEGMENT_BACKTEST_COLUMNS = tuple(SegmentBacktestRow.__dataclass_fields__)
SOURCE_COMPOSITION_COLUMNS = tuple(SourceCompositionRow.__dataclass_fields__)
EVENT_LEVEL_MAPPING_COLUMNS = tuple(EventLevelMappingRow.__dataclass_fields__)
DEFAULT_DIAGNOSTIC_FEATURE_CACHE_PATH = Path("outputs/cache/match_diagnostic_features.parquet")
DIAGNOSTIC_FEATURE_CACHE_SCHEMA_VERSION = 1

MISSINGNESS_FEATURE_COLUMNS = (
    "rank_log_diff",
    "overall_elo_diff",
    "surface_elo_diff",
    "prior_win_pct_diff",
    "recent_10_win_pct_diff",
    "rest_days_diff",
    "serve_points_won_pct_diff",
    "return_points_won_pct_diff",
)

DIAGNOSTIC_FEATURE_COLUMNS = tuple(
    dict.fromkeys(
        (
            "source_key",
            "tour",
            "match_date",
            "surface",
            "round",
            "best_of",
            "tournament_level",
            "player_a_won",
            "player_a_rank",
            "player_b_rank",
            *MODEL_FEATURE_COLUMNS,
        )
    )
)

CREATE_DIAGNOSTIC_TABLES_SQL = """
create schema if not exists tennis;

create table if not exists tennis.gold_prediction_calibration (
    model_name text not null,
    split text not null,
    probability_bin integer not null,
    bin_lower double precision not null,
    bin_upper double precision not null,
    sample_size integer not null,
    mean_predicted_probability double precision not null,
    observed_win_rate double precision not null,
    calibration_error double precision not null,
    evaluated_at timestamptz not null default now()
);

create table if not exists tennis.gold_feature_missingness (
    tour text not null,
    surface text not null,
    era text not null,
    stat_availability text not null,
    feature_name text not null,
    row_count integer not null,
    available_count integer not null,
    missing_count integer not null,
    missing_rate double precision not null,
    evaluated_at timestamptz not null default now()
);

create table if not exists tennis.gold_segment_backtests (
    model_name text not null,
    split text not null,
    tour text not null,
    surface text not null,
    match_format text not null,
    event_level text not null,
    draw_stage text not null,
    era text not null,
    ranking_coverage text not null,
    ranking_population text not null,
    source_coverage text not null,
    log_loss double precision not null,
    brier_score double precision not null,
    roc_auc double precision,
    accuracy double precision not null,
    sample_size integer not null,
    evaluated_at timestamptz not null default now()
);

create table if not exists tennis.gold_source_composition_diagnostics (
    split text not null,
    tour text not null,
    surface text not null,
    match_format text not null,
    event_level text not null,
    draw_stage text not null,
    era text not null,
    ranking_coverage text not null,
    ranking_population text not null,
    source_coverage text not null,
    source_key text not null,
    segment_sample_size integer not null,
    source_sample_size integer not null,
    source_share double precision not null,
    match_start date not null,
    match_end date not null,
    serve_return_available_rate double precision not null,
    both_ranked_rate double precision not null,
    logistic_log_loss double precision,
    logistic_roc_auc double precision,
    evaluated_at timestamptz not null default now()
);

create table if not exists tennis.gold_event_level_mapping_diagnostics (
    source_key text not null,
    tour text not null,
    tournament_level text not null,
    event_level text not null,
    row_count integer not null,
    is_mapped boolean not null,
    evaluated_at timestamptz not null default now()
);

alter table tennis.gold_segment_backtests
    add column if not exists event_level text;
alter table tennis.gold_segment_backtests
    add column if not exists draw_stage text;
alter table tennis.gold_segment_backtests
    add column if not exists ranking_population text;
alter table tennis.gold_segment_backtests
    add column if not exists source_coverage text;
alter table tennis.gold_source_composition_diagnostics
    add column if not exists event_level text;
alter table tennis.gold_source_composition_diagnostics
    add column if not exists draw_stage text;
alter table tennis.gold_source_composition_diagnostics
    add column if not exists ranking_population text;
alter table tennis.gold_source_composition_diagnostics
    add column if not exists source_coverage text;
"""


def build_prediction_diagnostics(
    frame: pd.DataFrame,
    *,
    probability_bins: int = 10,
    min_segment_size: int = 100,
    assume_safe: bool = False,
) -> DiagnosticBuildResult:
    predictions = predict_match_baseline_probabilities(
        frame,
        split=default_temporal_split(),
        assume_safe=assume_safe,
    )
    predictions = _add_segments(predictions)
    return DiagnosticBuildResult(
        calibration_rows=build_calibration_rows(predictions, probability_bins=probability_bins),
        missingness_rows=build_missingness_rows(predictions),
        segment_rows=build_segment_backtest_rows(predictions, min_segment_size=min_segment_size),
        source_composition_rows=build_source_composition_rows(
            predictions,
            min_segment_size=min_segment_size,
        ),
        event_mapping_rows=build_event_level_mapping_rows(predictions),
        calibration_plot_path=None,
    )


def build_calibration_rows(
    predictions: pd.DataFrame,
    *,
    probability_bins: int = 10,
) -> list[CalibrationRow]:
    rows: list[CalibrationRow] = []
    evaluation_frame = predictions[predictions["split"].isin(("validation", "test"))]
    edges = np.linspace(0.0, 1.0, probability_bins + 1)
    for model_name, probability_column in BASELINE_PROBABILITY_COLUMNS.items():
        if probability_column not in evaluation_frame:
            continue
        model_frame = evaluation_frame[
            evaluation_frame["split"].isin(evaluation_splits_for_model(model_name))
        ]
        for split_label, split_frame in model_frame.groupby("split", dropna=False):
            probabilities = split_frame[probability_column].astype(float)
            bins = pd.cut(
                probabilities,
                bins=edges,
                include_lowest=True,
                labels=False,
            )
            binned = split_frame.assign(_probability_bin=bins)
            for probability_bin, bin_frame in binned.groupby("_probability_bin", dropna=True):
                if bin_frame.empty:
                    continue
                bin_index = int(probability_bin)
                mean_probability = float(bin_frame[probability_column].mean())
                observed_rate = float(bin_frame["player_a_won"].astype(float).mean())
                rows.append(
                    CalibrationRow(
                        model_name=model_name,
                        split=str(split_label),
                        probability_bin=bin_index,
                        bin_lower=float(edges[bin_index]),
                        bin_upper=float(edges[bin_index + 1]),
                        sample_size=len(bin_frame),
                        mean_predicted_probability=mean_probability,
                        observed_win_rate=observed_rate,
                        calibration_error=observed_rate - mean_probability,
                    )
                )
    return rows


def build_missingness_rows(predictions: pd.DataFrame) -> list[MissingnessRow]:
    frame = _add_segments(predictions)
    rows: list[MissingnessRow] = []
    group_columns = ["tour", "surface_segment", "era", "stat_availability"]
    for group_values, group in frame.groupby(group_columns, dropna=False):
        tour, surface, era, stat_availability = (str(value) for value in group_values)
        row_count = len(group)
        for feature_name in MISSINGNESS_FEATURE_COLUMNS:
            available_count = int(group[feature_name].notna().sum())
            missing_count = row_count - available_count
            rows.append(
                MissingnessRow(
                    tour=tour,
                    surface=surface,
                    era=era,
                    stat_availability=stat_availability,
                    feature_name=feature_name,
                    row_count=row_count,
                    available_count=available_count,
                    missing_count=missing_count,
                    missing_rate=missing_count / row_count if row_count else 0.0,
                )
            )
    return rows


def build_segment_backtest_rows(
    predictions: pd.DataFrame,
    *,
    min_segment_size: int = 100,
) -> list[SegmentBacktestRow]:
    frame = _add_segments(predictions)
    frame = frame[frame["split"].isin(("validation", "test"))]
    group_columns = [
        "split",
        "tour",
        "surface_segment",
        "match_format",
        "event_level",
        "draw_stage",
        "era",
        "ranking_coverage",
        "ranking_population",
        "source_coverage",
    ]
    rows: list[SegmentBacktestRow] = []
    for group_values, group in frame.groupby(group_columns, dropna=False):
        if len(group) < min_segment_size:
            continue
        (
            split_label,
            tour,
            surface,
            match_format,
            event_level,
            draw_stage,
            era,
            ranking_coverage,
            ranking_population,
            source_coverage,
        ) = (
            str(value) for value in group_values
        )
        for model_name, probability_column in BASELINE_PROBABILITY_COLUMNS.items():
            if probability_column not in group:
                continue
            if split_label not in evaluation_splits_for_model(model_name):
                continue
            metrics = evaluate_binary_probabilities(
                group["player_a_won"].astype(bool).to_numpy(),
                group[probability_column].to_numpy(),
            )
            rows.append(
                SegmentBacktestRow(
                    model_name=model_name,
                    split=split_label,
                    tour=tour,
                    surface=surface,
                    match_format=match_format,
                    event_level=event_level,
                    draw_stage=draw_stage,
                    era=era,
                    ranking_coverage=ranking_coverage,
                    ranking_population=ranking_population,
                    source_coverage=source_coverage,
                    log_loss=metrics.log_loss,
                    brier_score=metrics.brier_score,
                    roc_auc=metrics.roc_auc,
                    accuracy=metrics.accuracy,
                    sample_size=metrics.sample_size,
                )
            )
    return rows


def build_source_composition_rows(
    predictions: pd.DataFrame,
    *,
    min_segment_size: int = 100,
) -> list[SourceCompositionRow]:
    frame = _add_segments(predictions)
    frame = frame[frame["split"].isin(("validation", "test"))].copy()
    if frame.empty:
        return []

    frame["source_key"] = frame["source_key"].fillna("unknown").astype(str)
    group_columns = [
        "split",
        "tour",
        "surface_segment",
        "match_format",
        "event_level",
        "draw_stage",
        "era",
        "ranking_coverage",
        "ranking_population",
        "source_coverage",
    ]
    rows: list[SourceCompositionRow] = []
    for group_values, segment in frame.groupby(group_columns, dropna=False):
        if len(segment) < min_segment_size:
            continue
        (
            split_label,
            tour,
            surface,
            match_format,
            event_level,
            draw_stage,
            era,
            ranking_coverage,
            ranking_population,
            source_coverage,
        ) = (
            str(value) for value in group_values
        )
        segment_sample_size = len(segment)
        for source_key, source_frame in segment.groupby("source_key", dropna=False):
            source_sample_size = len(source_frame)
            metrics = None
            if (
                "logistic_baseline_probability" in source_frame
                and source_frame["logistic_baseline_probability"].notna().all()
            ):
                metrics = evaluate_binary_probabilities(
                    source_frame["player_a_won"].astype(bool).to_numpy(),
                    source_frame["logistic_baseline_probability"].to_numpy(),
                )
            rows.append(
                SourceCompositionRow(
                    split=split_label,
                    tour=tour,
                    surface=surface,
                    match_format=match_format,
                    event_level=event_level,
                    draw_stage=draw_stage,
                    era=era,
                    ranking_coverage=ranking_coverage,
                    ranking_population=ranking_population,
                    source_coverage=source_coverage,
                    source_key=str(source_key),
                    segment_sample_size=segment_sample_size,
                    source_sample_size=source_sample_size,
                    source_share=source_sample_size / segment_sample_size,
                    match_start=source_frame["match_date"].min().date(),
                    match_end=source_frame["match_date"].max().date(),
                    serve_return_available_rate=float(
                        (
                            source_frame["serve_points_won_pct_diff"].notna()
                            & source_frame["return_points_won_pct_diff"].notna()
                        ).mean()
                    ),
                    both_ranked_rate=float(
                        (
                            source_frame["player_a_rank"].notna()
                            & source_frame["player_b_rank"].notna()
                        ).mean()
                    ),
                    logistic_log_loss=None if metrics is None else metrics.log_loss,
                    logistic_roc_auc=None if metrics is None else metrics.roc_auc,
                )
            )
    return rows


def build_event_level_mapping_rows(frame: pd.DataFrame) -> list[EventLevelMappingRow]:
    segmented = _add_segments(frame)
    working = segmented.loc[:, ["source_key", "tour", "tournament_level", "event_level"]].copy()
    working["source_key"] = working["source_key"].fillna("unknown").astype(str)
    working["tour"] = working["tour"].fillna("unknown").astype(str)
    working["tournament_level"] = working["tournament_level"].fillna("unknown").astype(str)
    rows: list[EventLevelMappingRow] = []
    for group_values, group in working.groupby(
        ["source_key", "tour", "tournament_level", "event_level"],
        dropna=False,
    ):
        source_key, tour, tournament_level, event_level = (str(value) for value in group_values)
        rows.append(
            EventLevelMappingRow(
                source_key=source_key,
                tour=tour,
                tournament_level=tournament_level,
                event_level=event_level,
                row_count=len(group),
                is_mapped=event_level != "unknown",
            )
        )
    rows.sort(key=lambda row: (not row.is_mapped, -row.row_count, row.source_key, row.tour))
    return rows


def _add_segments(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["match_date"] = pd.to_datetime(output["match_date"])
    output["tour"] = output["tour"].fillna("unknown").astype(str)
    output["surface_segment"] = (
        output["surface"].fillna("unknown").astype(str).str.strip().str.lower().replace("", "unknown")
    )
    output["match_format"] = output["best_of"].map(_match_format)
    tournament_level = output.get("tournament_level", pd.Series(pd.NA, index=output.index))
    round_value = output.get("round", pd.Series(pd.NA, index=output.index))
    output["event_level"] = [
        _event_level(level, tour=tour, source_key=source_key)
        for level, tour, source_key in zip(
            tournament_level,
            output["tour"],
            output["source_key"],
            strict=False,
        )
    ]
    output["draw_stage"] = round_value.map(_draw_stage)
    output["era"] = output["match_date"].dt.year.map(_era)
    output["ranking_coverage"] = np.where(
        output["player_a_rank"].notna() & output["player_b_rank"].notna(),
        "both_ranked",
        "missing_rank",
    )
    output["ranking_population"] = np.where(
        output["ranking_coverage"] == "both_ranked",
        "ranked_population",
        "incomplete_rankings",
    )
    output["source_coverage"] = output["source_key"].map(_source_coverage)
    output["stat_availability"] = np.select(
        [
            output["serve_points_won_pct_diff"].notna() & output["return_points_won_pct_diff"].notna(),
            output["serve_points_won_pct_diff"].notna() | output["return_points_won_pct_diff"].notna(),
        ],
        ["serve_and_return", "partial_serve_return"],
        default="no_serve_return",
    )
    return output


def _match_format(best_of: object) -> str:
    if pd.isna(best_of):
        return "unknown"
    try:
        return f"best_of_{int(float(str(best_of)))}"
    except (TypeError, ValueError):
        return "unknown"


def _event_level(
    tournament_level: object,
    *,
    tour: object = None,
    source_key: object = None,
) -> str:
    if pd.isna(tournament_level):
        return "unknown"
    value = str(tournament_level).strip().upper()
    tour_value = "" if pd.isna(tour) else str(tour).strip().lower()
    source_value = "" if pd.isna(source_key) else str(source_key).strip().lower()
    is_sackmann_source = (
        source_value.startswith("jeffsackmann_")
        or source_value == "aneeshers_tennis_sackmann_archive"
    )
    if value == "G":
        return "grand_slam"
    if value == "D":
        return "team_cup"
    if value == "O":
        return "olympics"
    if value == "E":
        return "exhibition"
    if value == "J":
        return "junior"
    if value == "T":
        return "team_tennis"
    if value == "F":
        return "season_final"
    if value in {"M", "A", "P", "PM", "P5", "I", "W"} or value.startswith("T"):
        return "tour_level"
    if value == "C":
        return "challenger_level"
    if value == "CC" and tour_value == "wta" and is_sackmann_source:
        return "itf_level"
    if value == "S" and tour_value == "atp" and is_sackmann_source:
        return "itf_level"
    if is_sackmann_source and _is_itf_prize_level(value):
        return "itf_level"
    return "unknown"


def _is_itf_prize_level(value: str) -> bool:
    normalized = value.removesuffix("+H")
    return normalized.isdigit()


def _draw_stage(round_value: object) -> str:
    if pd.isna(round_value):
        return "unknown"
    value = str(round_value).strip().upper()
    if value in {"Q1", "Q2", "Q3", "Q4", "QR"}:
        return "qualifying"
    if value in {"F", "SF", "QF", "R16", "R32", "R64", "R128", "RR", "BR"}:
        return "main_draw"
    return "unknown"


def _source_coverage(source_key: object) -> str:
    if pd.isna(source_key):
        return "unknown"
    value = str(source_key).strip().lower()
    if "archive" in value:
        return "fallback_archive"
    if value.startswith("jeffsackmann_") or value.startswith("tennisabstract_"):
        return "canonical"
    if "unverified" in value:
        return "unverified"
    return "other"


def _era(year: object) -> str:
    if pd.isna(year):
        return "unknown"
    year_int = int(float(str(year)))
    decade = year_int - (year_int % 10)
    return f"{decade}s"


def write_diagnostic_csvs(
    result: DiagnosticBuildResult,
    *,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_rows(output_dir / "match_prediction_calibration.csv", CALIBRATION_COLUMNS, result.calibration_rows)
    _write_rows(output_dir / "match_feature_missingness.csv", MISSINGNESS_COLUMNS, result.missingness_rows)
    _write_rows(output_dir / "match_segment_backtests.csv", SEGMENT_BACKTEST_COLUMNS, result.segment_rows)
    _write_rows(
        output_dir / "match_source_composition_diagnostics.csv",
        SOURCE_COMPOSITION_COLUMNS,
        result.source_composition_rows,
    )
    _write_rows(
        output_dir / "match_event_level_mapping.csv",
        EVENT_LEVEL_MAPPING_COLUMNS,
        result.event_mapping_rows,
    )


def write_calibration_plot(calibration_rows: list[CalibrationRow], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([row.__dict__ for row in calibration_rows])
    fig = go.Figure()
    if not frame.empty:
        for (model_name, split), group in frame.groupby(["model_name", "split"], dropna=False):
            fig.add_trace(
                go.Scatter(
                    x=group["mean_predicted_probability"],
                    y=group["observed_win_rate"],
                    mode="lines+markers",
                    name=f"{model_name} {split}",
                )
            )
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            name="perfect calibration",
            line={"dash": "dash", "color": "black"},
        )
    )
    fig.update_layout(
        title="Match Prediction Calibration",
        xaxis_title="Mean predicted probability",
        yaxis_title="Observed player A win rate",
        template="plotly_white",
    )
    fig.write_html(path)
    return path


def evaluate_match_diagnostics_postgres(
    *,
    output_dir: Path = Path("outputs/tables"),
    calibration_plot_path: Path = Path("outputs/charts/match_prediction_calibration.html"),
    persist_postgres: bool = True,
    conninfo: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = None,
    probability_bins: int = 10,
    min_segment_size: int = 100,
    feature_cache_path: Path | None = DEFAULT_DIAGNOSTIC_FEATURE_CACHE_PATH,
) -> DiagnosticBuildResult:
    assert_postgres_feature_table_safe_for_evaluation(
        conninfo=conninfo,
        start_date=start_date,
        end_date=end_date,
    )
    frame = load_diagnostic_features_frame(
        conninfo=conninfo,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        cache_path=feature_cache_path,
    )
    result = build_prediction_diagnostics(
        frame,
        probability_bins=probability_bins,
        min_segment_size=min_segment_size,
        assume_safe=True,
    )
    write_diagnostic_csvs(result, output_dir=output_dir)
    plot_path = write_calibration_plot(result.calibration_rows, calibration_plot_path)
    result = DiagnosticBuildResult(
        calibration_rows=result.calibration_rows,
        missingness_rows=result.missingness_rows,
        segment_rows=result.segment_rows,
        source_composition_rows=result.source_composition_rows,
        event_mapping_rows=result.event_mapping_rows,
        calibration_plot_path=plot_path,
    )
    if persist_postgres:
        persist_diagnostics_postgres(result, conninfo=conninfo)
    return result


def load_diagnostic_features_frame(
    *,
    conninfo: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = None,
    cache_path: Path | None = None,
) -> pd.DataFrame:
    import psycopg

    conditions = ["1 = 1"]
    filter_params: list[object] = []
    if start_date is not None:
        conditions.append("match_date >= %s")
        filter_params.append(start_date)
    if end_date is not None:
        conditions.append("match_date <= %s")
        filter_params.append(end_date)
    limit_sql = ""
    feature_params = list(filter_params)
    if limit is not None:
        limit_sql = " limit %s"
        feature_params.append(limit)
    with psycopg.connect(conninfo or PostgresSettings.from_env().conninfo) as connection:
        with connection.cursor() as cursor:
            snapshot = _diagnostic_feature_snapshot(cursor, conditions, filter_params)
            cache_metadata = _diagnostic_feature_cache_metadata(
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                snapshot=snapshot,
            )
            if cache_path is not None:
                cached = _load_diagnostic_feature_cache(cache_path, expected_metadata=cache_metadata)
                if cached is not None:
                    return cached

            frame = _query_diagnostic_features(cursor, conditions, feature_params, limit_sql)
            if cache_path is not None:
                _write_diagnostic_feature_cache(
                    frame,
                    cache_path=cache_path,
                    metadata=cache_metadata,
                )
            return frame


def _query_diagnostic_features(
    cursor: Any,
    conditions: Sequence[str],
    params: Sequence[object],
    limit_sql: str,
) -> pd.DataFrame:
    columns = ", ".join(DIAGNOSTIC_FEATURE_COLUMNS)
    sql = f"""
        select {columns}
        from tennis.gold_match_features_asof
        where {" and ".join(conditions)}
        order by match_date, tour, match_id
        {limit_sql}
    """
    cursor.execute(sql, list(params))
    if cursor.description is None:
        raise ValueError("Expected feature query to return columns")
    output_columns = [description.name for description in cursor.description]
    return pd.DataFrame(cursor.fetchall(), columns=output_columns)


def _diagnostic_feature_snapshot(
    cursor: Any,
    conditions: Sequence[str],
    params: Sequence[object],
) -> dict[str, object]:
    sql = f"""
        select
            count(*)::bigint as row_count,
            min(match_date)::text as min_match_date,
            max(match_date)::text as max_match_date,
            max(max_feature_asof_date)::text as max_feature_asof_date
        from tennis.gold_match_features_asof
        where {" and ".join(conditions)}
    """
    cursor.execute(sql, list(params))
    row = cursor.fetchone()
    if row is None:
        raise ValueError("Expected feature snapshot query to return one row")
    return {
        "row_count": int(row[0] or 0),
        "min_match_date": row[1],
        "max_match_date": row[2],
        "max_feature_asof_date": row[3],
    }


def _diagnostic_feature_cache_metadata(
    *,
    start_date: date | None,
    end_date: date | None,
    limit: int | None,
    snapshot: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": DIAGNOSTIC_FEATURE_CACHE_SCHEMA_VERSION,
        "source_table": "tennis.gold_match_features_asof",
        "columns": list(DIAGNOSTIC_FEATURE_COLUMNS),
        "filters": {
            "start_date": start_date.isoformat() if start_date is not None else None,
            "end_date": end_date.isoformat() if end_date is not None else None,
            "limit": limit,
        },
        "snapshot": snapshot,
    }


def _load_diagnostic_feature_cache(
    cache_path: Path,
    *,
    expected_metadata: dict[str, object],
) -> pd.DataFrame | None:
    metadata_path = _diagnostic_feature_cache_metadata_path(cache_path)
    if not cache_path.exists() or not metadata_path.exists():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if metadata != expected_metadata:
        return None
    return pd.read_parquet(cache_path)


def _write_diagnostic_feature_cache(
    frame: pd.DataFrame,
    *,
    cache_path: Path,
    metadata: dict[str, object],
) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(cache_path, index=False)
    _diagnostic_feature_cache_metadata_path(cache_path).write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _diagnostic_feature_cache_metadata_path(cache_path: Path) -> Path:
    return cache_path.with_suffix(cache_path.suffix + ".metadata.json")


def persist_diagnostics_postgres(
    result: DiagnosticBuildResult,
    *,
    conninfo: str | None = None,
) -> None:
    import psycopg

    with psycopg.connect(conninfo or PostgresSettings.from_env().conninfo) as connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_DIAGNOSTIC_TABLES_SQL)
            cursor.execute("truncate table tennis.gold_prediction_calibration")
            cursor.execute("truncate table tennis.gold_feature_missingness")
            cursor.execute("truncate table tennis.gold_segment_backtests")
            cursor.execute("truncate table tennis.gold_source_composition_diagnostics")
            cursor.execute("truncate table tennis.gold_event_level_mapping_diagnostics")
            _copy_dataclass_rows(
                cursor,
                "tennis.gold_prediction_calibration",
                CALIBRATION_COLUMNS,
                result.calibration_rows,
            )
            _copy_dataclass_rows(
                cursor,
                "tennis.gold_feature_missingness",
                MISSINGNESS_COLUMNS,
                result.missingness_rows,
            )
            _copy_dataclass_rows(
                cursor,
                "tennis.gold_segment_backtests",
                SEGMENT_BACKTEST_COLUMNS,
                result.segment_rows,
            )
            _copy_dataclass_rows(
                cursor,
                "tennis.gold_source_composition_diagnostics",
                SOURCE_COMPOSITION_COLUMNS,
                result.source_composition_rows,
            )
            _copy_dataclass_rows(
                cursor,
                "tennis.gold_event_level_mapping_diagnostics",
                EVENT_LEVEL_MAPPING_COLUMNS,
                result.event_mapping_rows,
            )
        connection.commit()


def _write_rows(path: Path, columns: tuple[str, ...], rows: Sequence[object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([getattr(row, column) for column in columns])


def _copy_dataclass_rows(
    cursor: Any,
    table_name: str,
    columns: tuple[str, ...],
    rows: Sequence[object],
) -> None:
    if not rows:
        return
    output = StringIO()
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    for row in rows:
        writer.writerow([_copy_value(getattr(row, column)) for column in columns])
    column_sql = ", ".join(columns)
    with cursor.copy(
        f"copy {table_name} ({column_sql}) from stdin with (format csv, delimiter E'\\t', null '\\N')"
    ) as copy:
        copy.write(output.getvalue())


def _copy_value(value: object) -> object:
    if value is None:
        return "\\N"
    if isinstance(value, float) and math.isnan(value):
        return "\\N"
    if isinstance(value, date):
        return value.isoformat()
    return value
