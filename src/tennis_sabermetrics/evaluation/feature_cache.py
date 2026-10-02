"""Snapshot-aware local caches for model-ready feature extracts."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

FEATURE_CACHE_SCHEMA_VERSION = 1


def feature_cache_metadata(
    *,
    source_table: str,
    columns: Sequence[str],
    filters: dict[str, object],
    snapshot: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": FEATURE_CACHE_SCHEMA_VERSION,
        "source_table": source_table,
        "columns": list(columns),
        "filters": _json_ready(filters),
        "snapshot": snapshot,
    }


def feature_table_snapshot(
    cursor: Any,
    *,
    source_table: str,
    conditions: Sequence[str],
    params: Sequence[object],
) -> dict[str, object]:
    sql = f"""
        select
            count(*)::bigint as row_count,
            min(match_date)::text as min_match_date,
            max(match_date)::text as max_match_date,
            max(max_feature_asof_date)::text as max_feature_asof_date
        from {source_table}
        where {" and ".join(conditions)}
    """
    cursor.execute(sql, list(params))
    row = cursor.fetchone()
    if row is None:
        raise ValueError(f"Expected snapshot query for {source_table} to return one row")
    return {
        "row_count": int(row[0] or 0),
        "min_match_date": row[1],
        "max_match_date": row[2],
        "max_feature_asof_date": row[3],
    }


def load_feature_cache(
    cache_path: Path,
    *,
    expected_metadata: dict[str, object],
) -> pd.DataFrame | None:
    metadata_path = feature_cache_metadata_path(cache_path)
    if not cache_path.exists() or not metadata_path.exists():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if metadata != expected_metadata:
        return None
    return pd.read_parquet(cache_path)


def write_feature_cache(
    frame: pd.DataFrame,
    *,
    cache_path: Path,
    metadata: dict[str, object],
) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(cache_path, index=False)
    feature_cache_metadata_path(cache_path).write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def feature_cache_metadata_path(cache_path: Path) -> Path:
    return cache_path.with_suffix(cache_path.suffix + ".metadata.json")


def _json_ready(values: dict[str, object]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, value in values.items():
        if isinstance(value, date):
            output[key] = value.isoformat()
        else:
            output[key] = value
    return output
