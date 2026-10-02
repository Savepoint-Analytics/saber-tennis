"""Walk-forward evaluation for match prediction baselines."""

from __future__ import annotations

import csv
import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from sklearn.impute import SimpleImputer  # type: ignore[import-untyped]
from sklearn.isotonic import IsotonicRegression  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]
from sklearn.preprocessing import StandardScaler  # type: ignore[import-untyped]

from tennis_sabermetrics.config import PostgresSettings
from tennis_sabermetrics.evaluation.feature_cache import (
    feature_cache_metadata,
    feature_table_snapshot,
    load_feature_cache,
    write_feature_cache,
)
from tennis_sabermetrics.evaluation.leakage_checks import (
    assert_feature_frame_safe_for_evaluation,
    assert_postgres_feature_table_safe_for_evaluation,
)
from tennis_sabermetrics.evaluation.metrics import evaluate_binary_probabilities
from tennis_sabermetrics.evaluation.temporal_split import TemporalSplit
from tennis_sabermetrics.models.match_outcome import (
    BASE_PROBABILITY_COLUMNS,
    BASE_TO_ISOTONIC_PROBABILITY_COLUMNS,
    BASE_TO_PLATT_PROBABILITY_COLUMNS,
    BASELINE_PROBABILITY_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    _probability_logit,
    elo_probability,
    ranking_baseline_probability,
)


@dataclass(frozen=True)
class WalkForwardEvaluationRow:
    window_label: str
    model_name: str
    split: str
    log_loss: float
    brier_score: float
    roc_auc: float | None
    accuracy: float
    sample_size: int
    train_start: date | None
    train_end: date
    validation_start: date
    validation_end: date
    test_start: date
    test_end: date | None


@dataclass(frozen=True)
class _PreparedWalkForwardFrame:
    match_ordinals: np.ndarray
    y: np.ndarray
    features: np.ndarray
    base_probabilities: dict[str, np.ndarray]


WALK_FORWARD_EVALUATION_COLUMNS = tuple(WalkForwardEvaluationRow.__dataclass_fields__)
WALK_FORWARD_FEATURE_COLUMNS = tuple(dict.fromkeys(("match_date", "player_a_won", *MODEL_FEATURE_COLUMNS)))
DEFAULT_WALK_FORWARD_FEATURE_CACHE_PATH = Path("outputs/cache/match_walk_forward_features.parquet")
WALK_FORWARD_SOURCE_TABLE = "tennis.gold_match_features_asof"

CREATE_WALK_FORWARD_TABLE_SQL = """
create schema if not exists tennis;

create table if not exists tennis.gold_prediction_walk_forward_backtests (
    window_label text not null,
    model_name text not null,
    split text not null,
    log_loss double precision not null,
    brier_score double precision not null,
    roc_auc double precision,
    accuracy double precision not null,
    sample_size integer not null,
    train_start date,
    train_end date not null,
    validation_start date not null,
    validation_end date not null,
    test_start date not null,
    test_end date,
    evaluated_at timestamptz not null default now()
);
"""


def default_walk_forward_splits(
    *,
    first_test_year: int = 2016,
    last_test_year: int = 2025,
    train_start: date = date(1990, 1, 1),
    validation_years: int = 3,
) -> list[TemporalSplit]:
    """Create expanding-train, rolling-validation, one-year-test split windows."""

    if validation_years < 1:
        raise ValueError("validation_years must be positive")
    if last_test_year < first_test_year:
        raise ValueError("last_test_year must be greater than or equal to first_test_year")

    splits: list[TemporalSplit] = []
    for test_year in range(first_test_year, last_test_year + 1):
        validation_start_year = test_year - validation_years
        split = TemporalSplit(
            train_start=train_start,
            train_end=date(validation_start_year - 1, 12, 31),
            validation_start=date(validation_start_year, 1, 1),
            validation_end=date(test_year - 1, 12, 31),
            test_start=date(test_year, 1, 1),
            test_end=date(test_year, 12, 31),
        )
        split.validate()
        splits.append(split)
    return splits


def evaluate_walk_forward_baselines(
    frame: pd.DataFrame,
    *,
    splits: Sequence[TemporalSplit] | None = None,
    assume_safe: bool = False,
) -> list[WalkForwardEvaluationRow]:
    """Evaluate baseline models across multiple temporal windows."""

    if not assume_safe:
        assert_feature_frame_safe_for_evaluation(frame)
    prepared = _prepare_static_probability_frame(frame)
    rows: list[WalkForwardEvaluationRow] = []
    for split in splits or default_walk_forward_splits():
        window_predictions = _predict_for_split(prepared, split)
        y_test = window_predictions.pop("player_a_won")
        if y_test.size == 0:
            continue
        for model_name, probability_column in BASELINE_PROBABILITY_COLUMNS.items():
            if probability_column not in window_predictions:
                continue
            metrics = evaluate_binary_probabilities(
                y_test.astype(bool),
                window_predictions[probability_column],
            )
            rows.append(
                WalkForwardEvaluationRow(
                    window_label=f"{split.test_start.year}",
                    model_name=model_name,
                    split="test",
                    log_loss=metrics.log_loss,
                    brier_score=metrics.brier_score,
                    roc_auc=metrics.roc_auc,
                    accuracy=metrics.accuracy,
                    sample_size=metrics.sample_size,
                    train_start=split.train_start,
                    train_end=split.train_end,
                    validation_start=split.validation_start,
                    validation_end=split.validation_end,
                    test_start=split.test_start,
                    test_end=split.test_end,
                )
            )
    return rows


def _prepare_static_probability_frame(frame: pd.DataFrame) -> _PreparedWalkForwardFrame:
    match_dates = pd.to_datetime(frame["match_date"])
    match_ordinals = match_dates.map(lambda value: value.date().toordinal()).to_numpy(
        dtype=np.int64
    )
    features = frame.loc[:, list(MODEL_FEATURE_COLUMNS)].to_numpy(dtype=float, copy=True)
    base_probabilities = {
        BASE_PROBABILITY_COLUMNS["ranking_log_difference"]: ranking_baseline_probability(
            frame["rank_log_diff"]
        ),
        BASE_PROBABILITY_COLUMNS["overall_elo"]: elo_probability(frame["overall_elo_diff"]),
        BASE_PROBABILITY_COLUMNS["surface_elo"]: elo_probability(frame["surface_elo_diff"]),
    }
    return _PreparedWalkForwardFrame(
        match_ordinals=match_ordinals,
        y=frame["player_a_won"].astype(int).to_numpy(),
        features=features,
        base_probabilities=base_probabilities,
    )


def _predict_for_split(
    prepared: _PreparedWalkForwardFrame,
    split: TemporalSplit,
) -> dict[str, np.ndarray]:
    train_start = date.min.toordinal() if split.train_start is None else split.train_start.toordinal()
    train_end = split.train_end.toordinal()
    validation_start = split.validation_start.toordinal()
    validation_end = split.validation_end.toordinal()
    test_start = split.test_start.toordinal()
    test_end = date.max.toordinal() if split.test_end is None else split.test_end.toordinal()
    ordinals = prepared.match_ordinals
    train_mask = (ordinals >= train_start) & (ordinals <= train_end)
    validation_mask = (ordinals >= validation_start) & (ordinals <= validation_end)
    test_mask = (ordinals >= test_start) & (ordinals <= test_end)

    y_train = prepared.y[train_mask]
    y_validation = prepared.y[validation_mask]
    y_test = prepared.y[test_mask]
    output: dict[str, np.ndarray] = {"player_a_won": y_test}

    for probability_column, probabilities in prepared.base_probabilities.items():
        output[probability_column] = probabilities[test_mask]

    if y_train.size > 0 and np.unique(y_train).size >= 2:
        model = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        )
        model.fit(prepared.features[train_mask], y_train)
        logistic_column = BASE_PROBABILITY_COLUMNS["logistic_baseline"]
        validation_logistic = model.predict_proba(prepared.features[validation_mask])[:, 1]
        test_logistic = model.predict_proba(prepared.features[test_mask])[:, 1]
        output[logistic_column] = test_logistic
        base_validation_probabilities = {
            **{
                probability_column: probabilities[validation_mask]
                for probability_column, probabilities in prepared.base_probabilities.items()
            },
            logistic_column: validation_logistic,
        }
    else:
        base_validation_probabilities = {
            probability_column: probabilities[validation_mask]
            for probability_column, probabilities in prepared.base_probabilities.items()
        }

    if y_validation.size == 0 or np.unique(y_validation).size < 2:
        return output

    for model_name, probability_column in BASE_PROBABILITY_COLUMNS.items():
        validation_probabilities = base_validation_probabilities.get(probability_column)
        test_probabilities = output.get(probability_column)
        if validation_probabilities is None or test_probabilities is None:
            continue
        calibrated = _calibrate_test_probabilities(
            validation_probabilities=validation_probabilities,
            y_validation=y_validation,
            test_probabilities=test_probabilities,
        )
        if calibrated is None:
            continue
        platt_probabilities, isotonic_probabilities = calibrated
        output[BASE_TO_PLATT_PROBABILITY_COLUMNS[model_name]] = platt_probabilities
        output[BASE_TO_ISOTONIC_PROBABILITY_COLUMNS[model_name]] = isotonic_probabilities
    return output


def _calibrate_test_probabilities(
    *,
    validation_probabilities: np.ndarray,
    y_validation: np.ndarray,
    test_probabilities: np.ndarray,
) -> tuple[np.ndarray, np.ndarray] | None:
    valid_mask = ~np.isnan(validation_probabilities)
    if valid_mask.sum() == 0:
        return None
    valid_y = y_validation[valid_mask]
    if np.unique(valid_y).size < 2:
        return None

    platt = LogisticRegression(max_iter=1000, random_state=42)
    platt.fit(_probability_logit(pd.Series(validation_probabilities[valid_mask])), valid_y)

    test_mask = ~np.isnan(test_probabilities)
    platt_output = np.full(test_probabilities.shape, np.nan, dtype=float)
    isotonic_output = np.full(test_probabilities.shape, np.nan, dtype=float)
    if test_mask.any():
        platt_output[test_mask] = platt.predict_proba(
            _probability_logit(pd.Series(test_probabilities[test_mask]))
        )[:, 1]
        isotonic = IsotonicRegression(out_of_bounds="clip")
        isotonic.fit(validation_probabilities[valid_mask], valid_y)
        isotonic_output[test_mask] = isotonic.predict(test_probabilities[test_mask])
    return platt_output, isotonic_output


def evaluate_walk_forward_postgres(
    *,
    output_path: Path | None = Path("outputs/tables/match_walk_forward_evaluation.csv"),
    persist_postgres: bool = True,
    conninfo: str | None = None,
    first_test_year: int = 2016,
    last_test_year: int = 2025,
    validation_years: int = 3,
    limit: int | None = None,
    feature_cache_path: Path | None = DEFAULT_WALK_FORWARD_FEATURE_CACHE_PATH,
) -> list[WalkForwardEvaluationRow]:
    splits = default_walk_forward_splits(
        first_test_year=first_test_year,
        last_test_year=last_test_year,
        validation_years=validation_years,
    )
    assert_postgres_feature_table_safe_for_evaluation(conninfo=conninfo)
    frame = load_walk_forward_features_frame(
        conninfo=conninfo,
        limit=limit,
        cache_path=feature_cache_path,
    )
    rows = evaluate_walk_forward_baselines(frame, splits=splits, assume_safe=True)
    if output_path is not None:
        write_walk_forward_csv(rows, output_path)
    if persist_postgres:
        persist_walk_forward_rows(rows, conninfo=conninfo)
    return rows


def load_walk_forward_features_frame(
    *,
    conninfo: str | None = None,
    limit: int | None = None,
    cache_path: Path | None = None,
) -> pd.DataFrame:
    import psycopg

    conditions = ["1 = 1"]
    filter_params: list[object] = []
    feature_params: list[object] = []
    limit_sql = ""
    if limit is not None:
        limit_sql = " limit %s"
        feature_params.append(limit)
    with psycopg.connect(conninfo or PostgresSettings.from_env().conninfo) as connection:
        with connection.cursor() as cursor:
            snapshot = feature_table_snapshot(
                cursor,
                source_table=WALK_FORWARD_SOURCE_TABLE,
                conditions=conditions,
                params=filter_params,
            )
            metadata = feature_cache_metadata(
                source_table=WALK_FORWARD_SOURCE_TABLE,
                columns=WALK_FORWARD_FEATURE_COLUMNS,
                filters={"limit": limit},
                snapshot=snapshot,
            )
            if cache_path is not None:
                cached = load_feature_cache(cache_path, expected_metadata=metadata)
                if cached is not None:
                    return cached

            frame = _query_walk_forward_features(cursor, feature_params, limit_sql)
            if cache_path is not None:
                write_feature_cache(frame, cache_path=cache_path, metadata=metadata)
            return frame


def _query_walk_forward_features(
    cursor: Any,
    params: Sequence[object],
    limit_sql: str,
) -> pd.DataFrame:
    columns = ", ".join(WALK_FORWARD_FEATURE_COLUMNS)
    sql = f"""
        select {columns}
        from {WALK_FORWARD_SOURCE_TABLE}
        order by match_date, tour, match_id
        {limit_sql}
    """
    cursor.execute(sql, list(params))
    if cursor.description is None:
        raise ValueError("Expected feature query to return columns")
    output_columns = [description.name for description in cursor.description]
    return pd.DataFrame(cursor.fetchall(), columns=output_columns)


def write_walk_forward_csv(rows: Sequence[WalkForwardEvaluationRow], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(WALK_FORWARD_EVALUATION_COLUMNS)
        for row in rows:
            writer.writerow([getattr(row, column) for column in WALK_FORWARD_EVALUATION_COLUMNS])
    return len(rows)


def persist_walk_forward_rows(
    rows: Sequence[WalkForwardEvaluationRow],
    *,
    conninfo: str | None = None,
) -> int:
    import psycopg

    with psycopg.connect(conninfo or PostgresSettings.from_env().conninfo) as connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_WALK_FORWARD_TABLE_SQL)
            cursor.execute("truncate table tennis.gold_prediction_walk_forward_backtests")
            _copy_dataclass_rows(
                cursor,
                "tennis.gold_prediction_walk_forward_backtests",
                WALK_FORWARD_EVALUATION_COLUMNS,
                rows,
            )
        connection.commit()
    return len(rows)


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
