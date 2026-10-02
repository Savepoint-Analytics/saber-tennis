"""Bronze-layer conversion helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from tennis_sabermetrics.config import FALLBACK_ARCHIVE_SOURCE_KEY, GIT_SOURCES, ProjectPaths
from tennis_sabermetrics.ingest.git_sources import repo_dir_name
from tennis_sabermetrics.ingest.tennis_atp import (
    iter_atp_match_csvs,
    iter_atp_player_csvs,
    iter_atp_ranking_csvs,
)
from tennis_sabermetrics.ingest.tennis_wta import (
    iter_wta_match_csvs,
    iter_wta_player_csvs,
    iter_wta_ranking_csvs,
)

BRONZE_REQUIRED_COLUMNS: dict[str, frozenset[str]] = {
    "matches": frozenset(
        {
            "tourney_id",
            "tourney_date",
            "match_num",
            "winner_id",
            "loser_id",
            "score",
            "_source_key",
            "_source_url",
            "_source_commit_sha",
            "_snapshot_date",
            "_ingested_at",
            "_license_name",
            "_tour",
        }
    ),
    "rankings": frozenset(
        {
            "0",
            "1",
            "2",
            "3",
            "_source_key",
            "_source_url",
            "_source_commit_sha",
            "_snapshot_date",
            "_ingested_at",
            "_license_name",
            "_tour",
        }
    ),
    "players": frozenset(
        {
            "player_id",
            "name_first",
            "name_last",
            "hand",
            "dob",
            "ioc",
            "height",
            "_source_key",
            "_source_url",
            "_source_commit_sha",
            "_snapshot_date",
            "_ingested_at",
            "_license_name",
            "_tour",
        }
    ),
}


@dataclass(frozen=True)
class BronzeMetadata:
    source_key: str
    source_url: str
    source_commit_sha: str | None
    snapshot_date: date
    license_name: str | None
    ingested_at: datetime
    tour: str | None = None

    @classmethod
    def from_source(
        cls,
        *,
        source_key: str,
        source_url: str,
        snapshot_date: date,
        source_commit_sha: str | None = None,
        license_name: str | None = None,
        tour: str | None = None,
    ) -> BronzeMetadata:
        return cls(
            source_key=source_key,
            source_url=source_url,
            source_commit_sha=source_commit_sha,
            snapshot_date=snapshot_date,
            license_name=license_name,
            ingested_at=datetime.now(UTC),
            tour=tour,
        )


@dataclass(frozen=True)
class BronzeBuildResult:
    source_file_path: Path
    parquet_path: Path
    table_name: str
    row_count: int


@dataclass(frozen=True)
class BronzeSchemaValidationResult:
    parquet_path: Path
    table_name: str
    row_count: int
    missing_columns: tuple[str, ...]
    unparseable_date_columns: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.missing_columns and not self.unparseable_date_columns and self.row_count > 0


def convert_csv_to_bronze_parquet(
    csv_path: Path,
    parquet_path: Path,
    metadata: BronzeMetadata,
    *,
    read_csv_kwargs: dict[str, Any] | None = None,
) -> int:
    """Convert a source CSV to Parquet and append required bronze metadata columns."""

    import pandas as pd  # type: ignore[import-untyped]

    csv_options: dict[str, Any] = {"dtype": "string", "low_memory": False}
    csv_options.update(read_csv_kwargs or {})
    frame = pd.read_csv(csv_path, **csv_options)
    frame.columns = [str(column) for column in frame.columns]
    frame["_source_key"] = metadata.source_key
    frame["_source_url"] = metadata.source_url
    frame["_source_commit_sha"] = metadata.source_commit_sha
    frame["_snapshot_date"] = metadata.snapshot_date.isoformat()
    frame["_ingested_at"] = metadata.ingested_at.isoformat()
    frame["_license_name"] = metadata.license_name
    if metadata.tour:
        frame["_tour"] = metadata.tour

    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(parquet_path, index=False)
    return len(frame)


def _source_files_for_bronze(source_key: str, source_root: Path) -> dict[str, list[Path]]:
    if source_key == "jeffsackmann_tennis_atp":
        return {
            "players": iter_atp_player_csvs(source_root),
            "matches": iter_atp_match_csvs(source_root),
            "rankings": iter_atp_ranking_csvs(source_root),
        }
    if source_key == "jeffsackmann_tennis_wta":
        return {
            "players": iter_wta_player_csvs(source_root),
            "matches": iter_wta_match_csvs(source_root),
            "rankings": iter_wta_ranking_csvs(source_root),
        }
    raise ValueError(f"Bronze conversion is not implemented for source {source_key!r}")


def _archive_tour_root(source_root: Path, archive_tour: str) -> Path:
    if source_root.name == archive_tour:
        return source_root
    return source_root / archive_tour


def _source_files_for_archive_tour(source_root: Path, archive_tour: str) -> dict[str, list[Path]]:
    tour_root = _archive_tour_root(source_root, archive_tour)
    if archive_tour == "atp":
        return {
            "players": iter_atp_player_csvs(tour_root),
            "matches": iter_atp_match_csvs(tour_root),
            "rankings": iter_atp_ranking_csvs(tour_root),
        }
    if archive_tour == "wta":
        return {
            "players": iter_wta_player_csvs(tour_root),
            "matches": iter_wta_match_csvs(tour_root),
            "rankings": iter_wta_ranking_csvs(tour_root),
        }
    raise ValueError(f"Unsupported archive tour: {archive_tour!r}")


def default_source_root(source_key: str) -> Path:
    try:
        source = GIT_SOURCES[source_key]
    except KeyError as exc:
        raise ValueError(f"Unknown Git source key: {source_key}") from exc
    return ProjectPaths.from_env().external_repos_root / repo_dir_name(source)


def default_bronze_root() -> Path:
    return ProjectPaths.from_env().bronze_data_root


def build_bronze_for_source(
    *,
    source_key: str,
    snapshot_date: date,
    source_root: Path | None = None,
    bronze_root: Path | None = None,
    source_commit_sha: str | None = None,
    archive_tour: str | None = None,
) -> list[BronzeBuildResult]:
    if source_key not in GIT_SOURCES:
        raise ValueError(f"Unknown Git source key: {source_key}")
    if source_key == FALLBACK_ARCHIVE_SOURCE_KEY and not archive_tour:
        raise ValueError("--archive-tour is required for fallback archive bronze conversion")
    if source_key != FALLBACK_ARCHIVE_SOURCE_KEY and archive_tour:
        raise ValueError("--archive-tour is only valid for fallback archive bronze conversion")
    source = GIT_SOURCES[source_key]
    resolved_source_root = source_root or default_source_root(source_key)
    resolved_bronze_root = bronze_root or default_bronze_root()
    if not resolved_source_root.exists():
        raise FileNotFoundError(
            f"Source root {resolved_source_root} does not exist. Run sync-sources first or pass "
            "--source-root."
        )

    metadata = BronzeMetadata.from_source(
        source_key=source.source_key,
        source_url=source.source_url,
        source_commit_sha=source_commit_sha,
        snapshot_date=snapshot_date,
        license_name=source.license_name,
        tour=archive_tour,
    )

    results: list[BronzeBuildResult] = []
    source_files = (
        _source_files_for_archive_tour(resolved_source_root, archive_tour)
        if archive_tour
        else _source_files_for_bronze(source_key, resolved_source_root)
    )
    for table_name, csv_paths in source_files.items():
        for csv_path in csv_paths:
            source_path_parts = [source_key]
            if archive_tour:
                source_path_parts.append(archive_tour)
            parquet_path = (
                resolved_bronze_root
                / Path(*source_path_parts)
                / table_name
                / f"snapshot_date={snapshot_date.isoformat()}"
                / f"{csv_path.stem}.parquet"
            )
            read_csv_kwargs = {"header": None} if table_name == "rankings" else None
            row_count = convert_csv_to_bronze_parquet(
                csv_path,
                parquet_path,
                metadata,
                read_csv_kwargs=read_csv_kwargs,
            )
            results.append(
                BronzeBuildResult(
                    source_file_path=csv_path,
                    parquet_path=parquet_path,
                    table_name=table_name,
                    row_count=row_count,
                )
            )
    return results


def validate_bronze_schema(
    parquet_path: Path,
    *,
    table_name: str,
) -> BronzeSchemaValidationResult:
    """Validate required bronze metadata/source columns and parseable dates."""

    import pandas as pd  # type: ignore[import-untyped]

    frame = pd.read_parquet(parquet_path)
    required_columns = BRONZE_REQUIRED_COLUMNS[table_name]
    missing_columns = tuple(sorted(required_columns.difference(str(column) for column in frame.columns)))
    unparseable: list[str] = []
    if "_snapshot_date" in frame:
        parsed_snapshot = pd.to_datetime(frame["_snapshot_date"], errors="coerce")
        if parsed_snapshot.isna().any():
            unparseable.append("_snapshot_date")
    if table_name == "matches" and "tourney_date" in frame:
        parsed_match_dates = pd.to_datetime(frame["tourney_date"], format="%Y%m%d", errors="coerce")
        if parsed_match_dates.isna().any():
            unparseable.append("tourney_date")
    if table_name == "rankings" and "0" in frame:
        parsed_ranking_dates = pd.to_datetime(frame["0"], format="%Y%m%d", errors="coerce")
        invalid_dates = frame.loc[parsed_ranking_dates.isna(), "0"].astype("string")
        allowed_header_only = len(invalid_dates) == 1 and invalid_dates.iloc[0] == "ranking_date"
        if parsed_ranking_dates.isna().any() and not allowed_header_only:
            unparseable.append("0")
    return BronzeSchemaValidationResult(
        parquet_path=parquet_path,
        table_name=table_name,
        row_count=len(frame),
        missing_columns=missing_columns,
        unparseable_date_columns=tuple(unparseable),
    )
