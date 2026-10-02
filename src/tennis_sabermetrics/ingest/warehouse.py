"""PostgreSQL bronze landing-table loaders."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from tennis_sabermetrics.config import FALLBACK_ARCHIVE_SOURCE_KEY, PostgresSettings

POSTGRES_TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "tennis.bronze_matches": (
        "source_key",
        "tour",
        "match_id",
        "tourney_id",
        "tourney_date",
        "surface",
        "round",
        "best_of",
        "winner_id",
        "loser_id",
        "score",
        "minutes",
        "source_commit_sha",
        "snapshot_date",
    ),
    "tennis.bronze_rankings": (
        "source_key",
        "tour",
        "ranking_date",
        "rank",
        "player_id",
        "ranking_points",
        "source_commit_sha",
        "snapshot_date",
    ),
    "tennis.bronze_players": (
        "source_key",
        "tour",
        "player_id",
        "name_first",
        "name_last",
        "hand",
        "dob",
        "ioc",
        "height_cm",
        "source_commit_sha",
        "snapshot_date",
    ),
    "tennis.bronze_tournaments": (
        "source_key",
        "tour",
        "tourney_id",
        "tourney_name",
        "surface",
        "draw_size",
        "tourney_level",
        "tourney_date",
        "source_commit_sha",
        "snapshot_date",
    ),
    "tennis.bronze_match_stats": (
        "source_key",
        "tour",
        "match_id",
        "player_id",
        "opponent_id",
        "is_winner",
        "aces",
        "double_faults",
        "first_serves_in",
        "first_serves_total",
        "first_serve_points_won",
        "first_serve_points_total",
        "second_serve_points_won",
        "second_serve_points_total",
        "break_points_saved",
        "break_points_faced",
        "source_commit_sha",
        "snapshot_date",
    ),
}


CREATE_BRONZE_TABLE_SQL = """
create schema if not exists tennis;

create table if not exists tennis.bronze_matches (
    source_key text not null,
    tour text not null,
    match_id text not null,
    tourney_id text,
    tourney_date date,
    surface text,
    round text,
    best_of integer,
    winner_id text,
    loser_id text,
    score text,
    minutes integer,
    source_commit_sha text,
    snapshot_date date not null
);

create table if not exists tennis.bronze_rankings (
    source_key text not null,
    tour text not null,
    ranking_date date,
    rank integer,
    player_id text,
    ranking_points integer,
    source_commit_sha text,
    snapshot_date date not null
);

create table if not exists tennis.bronze_players (
    source_key text not null,
    tour text not null,
    player_id text,
    name_first text,
    name_last text,
    hand text,
    dob date,
    ioc text,
    height_cm integer,
    source_commit_sha text,
    snapshot_date date not null
);

create table if not exists tennis.bronze_tournaments (
    source_key text not null,
    tour text not null,
    tourney_id text,
    tourney_name text,
    surface text,
    draw_size text,
    tourney_level text,
    tourney_date date,
    source_commit_sha text,
    snapshot_date date not null
);

create table if not exists tennis.bronze_match_stats (
    source_key text not null,
    tour text not null,
    match_id text not null,
    player_id text,
    opponent_id text,
    is_winner boolean,
    aces integer,
    double_faults integer,
    first_serves_in integer,
    first_serves_total integer,
    first_serve_points_won integer,
    first_serve_points_total integer,
    second_serve_points_won integer,
    second_serve_points_total integer,
    break_points_saved integer,
    break_points_faced integer,
    source_commit_sha text,
    snapshot_date date not null
);
"""


@dataclass(frozen=True)
class BronzeWarehouseLoadResult:
    table_name: str
    row_count: int


@dataclass(frozen=True)
class RawManifestRowCountResult:
    updated_count: int
    missing_count: int


def _nullable_text(series: pd.Series) -> pd.Series:
    return series.astype("string").replace({"": pd.NA})


def _optional_column(frame: pd.DataFrame, column: str) -> pd.Series:
    if column in frame:
        return _nullable_text(frame[column])
    return pd.Series(pd.NA, index=frame.index, dtype="string")


def _optional_int(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(_optional_column(frame, column), errors="coerce").astype("Int64")


def _yyyymmdd(series: pd.Series) -> pd.Series:
    return pd.to_datetime(_nullable_text(series), format="%Y%m%d", errors="coerce").dt.date


def _match_ids(frame: pd.DataFrame) -> pd.Series:
    return (
        _optional_column(frame, "_tour").fillna("")
        + ":"
        + _optional_column(frame, "tourney_id").fillna("")
        + ":"
        + _optional_column(frame, "match_num").fillna("")
    )


def matches_landing_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_key": _optional_column(frame, "_source_key"),
            "tour": _optional_column(frame, "_tour"),
            "match_id": _match_ids(frame),
            "tourney_id": _optional_column(frame, "tourney_id"),
            "tourney_date": _yyyymmdd(_optional_column(frame, "tourney_date")),
            "surface": _optional_column(frame, "surface"),
            "round": _optional_column(frame, "round"),
            "best_of": _optional_int(frame, "best_of"),
            "winner_id": _optional_column(frame, "winner_id"),
            "loser_id": _optional_column(frame, "loser_id"),
            "score": _optional_column(frame, "score"),
            "minutes": _optional_int(frame, "minutes"),
            "source_commit_sha": _optional_column(frame, "_source_commit_sha"),
            "snapshot_date": pd.to_datetime(
                _optional_column(frame, "_snapshot_date"), errors="coerce"
            ).dt.date,
        }
    )


def rankings_landing_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_key": _optional_column(frame, "_source_key"),
            "tour": _optional_column(frame, "_tour"),
            "ranking_date": _yyyymmdd(_optional_column(frame, "0")),
            "rank": _optional_int(frame, "1"),
            "player_id": _optional_column(frame, "2"),
            "ranking_points": _optional_int(frame, "3"),
            "source_commit_sha": _optional_column(frame, "_source_commit_sha"),
            "snapshot_date": pd.to_datetime(
                _optional_column(frame, "_snapshot_date"), errors="coerce"
            ).dt.date,
        }
    )


def tournaments_landing_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_key": _optional_column(frame, "_source_key"),
            "tour": _optional_column(frame, "_tour"),
            "tourney_id": _optional_column(frame, "tourney_id"),
            "tourney_name": _optional_column(frame, "tourney_name"),
            "surface": _optional_column(frame, "surface"),
            "draw_size": _optional_column(frame, "draw_size"),
            "tourney_level": _optional_column(frame, "tourney_level"),
            "tourney_date": _yyyymmdd(_optional_column(frame, "tourney_date")),
            "source_commit_sha": _optional_column(frame, "_source_commit_sha"),
            "snapshot_date": pd.to_datetime(
                _optional_column(frame, "_snapshot_date"), errors="coerce"
            ).dt.date,
        }
    ).drop_duplicates()


def players_landing_frame(frame: pd.DataFrame) -> pd.DataFrame:
    winner = pd.DataFrame(
        {
            "source_key": _optional_column(frame, "_source_key"),
            "tour": _optional_column(frame, "_tour"),
            "player_id": _optional_column(frame, "winner_id"),
            "name_first": pd.NA,
            "name_last": _optional_column(frame, "winner_name"),
            "hand": _optional_column(frame, "winner_hand"),
            "dob": pd.NaT,
            "ioc": _optional_column(frame, "winner_ioc"),
            "height_cm": _optional_int(frame, "winner_ht"),
            "source_commit_sha": _optional_column(frame, "_source_commit_sha"),
            "snapshot_date": pd.to_datetime(
                _optional_column(frame, "_snapshot_date"), errors="coerce"
            ).dt.date,
        }
    )
    loser = pd.DataFrame(
        {
            "source_key": _optional_column(frame, "_source_key"),
            "tour": _optional_column(frame, "_tour"),
            "player_id": _optional_column(frame, "loser_id"),
            "name_first": pd.NA,
            "name_last": _optional_column(frame, "loser_name"),
            "hand": _optional_column(frame, "loser_hand"),
            "dob": pd.NaT,
            "ioc": _optional_column(frame, "loser_ioc"),
            "height_cm": _optional_int(frame, "loser_ht"),
            "source_commit_sha": _optional_column(frame, "_source_commit_sha"),
            "snapshot_date": pd.to_datetime(
                _optional_column(frame, "_snapshot_date"), errors="coerce"
            ).dt.date,
        }
    )
    return pd.concat([winner, loser], ignore_index=True).drop_duplicates(
        subset=["source_key", "tour", "player_id", "name_last", "hand", "ioc", "height_cm"]
    )


def player_file_landing_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_key": _optional_column(frame, "_source_key"),
            "tour": _optional_column(frame, "_tour"),
            "player_id": _optional_column(frame, "player_id"),
            "name_first": _optional_column(frame, "name_first"),
            "name_last": _optional_column(frame, "name_last"),
            "hand": _optional_column(frame, "hand"),
            "dob": _yyyymmdd(_optional_column(frame, "dob")),
            "ioc": _optional_column(frame, "ioc"),
            "height_cm": _optional_int(frame, "height"),
            "source_commit_sha": _optional_column(frame, "_source_commit_sha"),
            "snapshot_date": pd.to_datetime(
                _optional_column(frame, "_snapshot_date"), errors="coerce"
            ).dt.date,
        }
    )


def match_stats_landing_frame(frame: pd.DataFrame) -> pd.DataFrame:
    base = {
        "source_key": _optional_column(frame, "_source_key"),
        "tour": _optional_column(frame, "_tour"),
        "match_id": _match_ids(frame),
        "source_commit_sha": _optional_column(frame, "_source_commit_sha"),
        "snapshot_date": pd.to_datetime(
            _optional_column(frame, "_snapshot_date"), errors="coerce"
        ).dt.date,
    }
    winner = pd.DataFrame(
        {
            **base,
            "player_id": _optional_column(frame, "winner_id"),
            "opponent_id": _optional_column(frame, "loser_id"),
            "is_winner": True,
            "aces": _optional_int(frame, "w_ace"),
            "double_faults": _optional_int(frame, "w_df"),
            "first_serves_in": _optional_int(frame, "w_1stIn"),
            "first_serves_total": _optional_int(frame, "w_svpt"),
            "first_serve_points_won": _optional_int(frame, "w_1stWon"),
            "first_serve_points_total": _optional_int(frame, "w_1stIn"),
            "second_serve_points_won": _optional_int(frame, "w_2ndWon"),
            "second_serve_points_total": _optional_int(frame, "w_svpt")
            - _optional_int(frame, "w_1stIn"),
            "break_points_saved": _optional_int(frame, "w_bpSaved"),
            "break_points_faced": _optional_int(frame, "w_bpFaced"),
        }
    )
    loser = pd.DataFrame(
        {
            **base,
            "player_id": _optional_column(frame, "loser_id"),
            "opponent_id": _optional_column(frame, "winner_id"),
            "is_winner": False,
            "aces": _optional_int(frame, "l_ace"),
            "double_faults": _optional_int(frame, "l_df"),
            "first_serves_in": _optional_int(frame, "l_1stIn"),
            "first_serves_total": _optional_int(frame, "l_svpt"),
            "first_serve_points_won": _optional_int(frame, "l_1stWon"),
            "first_serve_points_total": _optional_int(frame, "l_1stIn"),
            "second_serve_points_won": _optional_int(frame, "l_2ndWon"),
            "second_serve_points_total": _optional_int(frame, "l_svpt")
            - _optional_int(frame, "l_1stIn"),
            "break_points_saved": _optional_int(frame, "l_bpSaved"),
            "break_points_faced": _optional_int(frame, "l_bpFaced"),
        }
    )
    return pd.concat([winner, loser], ignore_index=True)


def _copy_frame(cursor: Any, table_name: str, frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    columns = POSTGRES_TABLE_COLUMNS[table_name]
    output = StringIO()
    frame.loc[:, columns].to_csv(
        output,
        index=False,
        header=False,
        sep="\t",
        na_rep="\\N",
        quoting=csv.QUOTE_MINIMAL,
    )
    column_sql = ", ".join(columns)
    with cursor.copy(f"copy {table_name} ({column_sql}) from stdin with (format csv, delimiter E'\\t', null '\\N')") as copy:
        copy.write(output.getvalue())
    return len(frame)


def _read_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def _bronze_files(bronze_root: Path, source_key: str, tour: str, table_name: str, snapshot_date: date) -> list[Path]:
    root = bronze_root / source_key / tour / table_name / f"snapshot_date={snapshot_date.isoformat()}"
    if not root.exists():
        return []
    return sorted(root.glob("*.parquet"))


def load_bronze_postgres(
    *,
    bronze_root: Path,
    snapshot_date: date,
    source_key: str = FALLBACK_ARCHIVE_SOURCE_KEY,
    tours: tuple[str, ...] = ("atp", "wta"),
    conninfo: str | None = None,
    replace: bool = True,
) -> list[BronzeWarehouseLoadResult]:
    """Load source-shaped bronze Parquet into PostgreSQL bronze landing tables."""

    import psycopg

    table_counts = {table_name: 0 for table_name in POSTGRES_TABLE_COLUMNS}
    with psycopg.connect(conninfo or PostgresSettings.from_env().conninfo) as connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_BRONZE_TABLE_SQL)
            if replace:
                for table_name in POSTGRES_TABLE_COLUMNS:
                    cursor.execute(f"truncate table {table_name}")

            for tour in tours:
                player_files = _bronze_files(bronze_root, source_key, tour, "players", snapshot_date)
                for path in player_files:
                    frame = _read_parquet(path)
                    table_counts["tennis.bronze_players"] += _copy_frame(
                        cursor,
                        "tennis.bronze_players",
                        player_file_landing_frame(frame),
                    )

                for path in _bronze_files(bronze_root, source_key, tour, "matches", snapshot_date):
                    frame = _read_parquet(path)
                    landing_frames = {
                        "tennis.bronze_matches": matches_landing_frame(frame),
                        "tennis.bronze_tournaments": tournaments_landing_frame(frame),
                        "tennis.bronze_match_stats": match_stats_landing_frame(frame),
                    }
                    if not player_files:
                        landing_frames["tennis.bronze_players"] = players_landing_frame(frame)
                    for table_name, landing_frame in landing_frames.items():
                        table_counts[table_name] += _copy_frame(cursor, table_name, landing_frame)

                for path in _bronze_files(bronze_root, source_key, tour, "rankings", snapshot_date):
                    frame = _read_parquet(path)
                    table_counts["tennis.bronze_rankings"] += _copy_frame(
                        cursor,
                        "tennis.bronze_rankings",
                        rankings_landing_frame(frame),
                    )
        connection.commit()
    return [
        BronzeWarehouseLoadResult(table_name=table_name, row_count=row_count)
        for table_name, row_count in table_counts.items()
    ]


def count_source_file_rows(path: Path) -> int | None:
    if path.suffix.lower() != ".csv":
        return None
    with path.open("rb") as file:
        line_count = sum(1 for _ in file)
    if line_count == 0:
        return 0
    if "rankings" in path.name:
        return line_count
    return max(line_count - 1, 0)


def enrich_raw_manifest_row_counts(
    *,
    source_root: Path,
    snapshot_date: date,
    source_key: str = FALLBACK_ARCHIVE_SOURCE_KEY,
    conninfo: str | None = None,
) -> RawManifestRowCountResult:
    import psycopg

    updated_count = 0
    missing_count = 0
    with psycopg.connect(conninfo or PostgresSettings.from_env().conninfo) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select source_file_path
                from tennis.raw_manifest
                where source_key = %s
                  and snapshot_date = %s
                """,
                (source_key, snapshot_date),
            )
            for (source_file_path,) in cursor.fetchall():
                row_count = count_source_file_rows(source_root / source_file_path)
                if row_count is None:
                    missing_count += 1
                    continue
                cursor.execute(
                    """
                    update tennis.raw_manifest
                    set row_count = %s
                    where source_key = %s
                      and snapshot_date = %s
                      and source_file_path = %s
                    """,
                    (row_count, source_key, snapshot_date, source_file_path),
                )
                updated_count += 1
        connection.commit()
    return RawManifestRowCountResult(updated_count=updated_count, missing_count=missing_count)
