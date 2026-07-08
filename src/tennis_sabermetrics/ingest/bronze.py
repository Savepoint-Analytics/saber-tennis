"""Bronze-layer conversion helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BronzeMetadata:
    source_key: str
    source_url: str
    source_commit_sha: str | None
    snapshot_date: date
    license_name: str | None
    ingested_at: datetime

    @classmethod
    def from_source(
        cls,
        *,
        source_key: str,
        source_url: str,
        snapshot_date: date,
        source_commit_sha: str | None = None,
        license_name: str | None = None,
    ) -> BronzeMetadata:
        return cls(
            source_key=source_key,
            source_url=source_url,
            source_commit_sha=source_commit_sha,
            snapshot_date=snapshot_date,
            license_name=license_name,
            ingested_at=datetime.now(UTC),
        )


def convert_csv_to_bronze_parquet(
    csv_path: Path,
    parquet_path: Path,
    metadata: BronzeMetadata,
    *,
    read_csv_kwargs: dict[str, Any] | None = None,
) -> int:
    """Convert a source CSV to Parquet and append required bronze metadata columns."""

    import pandas as pd  # type: ignore[import-untyped]

    frame = pd.read_csv(csv_path, **(read_csv_kwargs or {}))
    frame["_source_key"] = metadata.source_key
    frame["_source_url"] = metadata.source_url
    frame["_source_commit_sha"] = metadata.source_commit_sha
    frame["_snapshot_date"] = metadata.snapshot_date.isoformat()
    frame["_ingested_at"] = metadata.ingested_at.isoformat()
    frame["_license_name"] = metadata.license_name

    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(parquet_path, index=False)
    return len(frame)
