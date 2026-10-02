from datetime import date
from pathlib import Path

import pandas as pd

from tennis_sabermetrics.evaluation.feature_cache import (
    feature_cache_metadata,
    feature_cache_metadata_path,
    load_feature_cache,
    write_feature_cache,
)


def test_feature_cache_round_trips_when_metadata_matches(tmp_path: Path) -> None:
    cache_path = tmp_path / "features.parquet"
    frame = pd.DataFrame({"match_date": [date(2024, 1, 1)], "rank_log_diff": [0.42]})
    metadata = feature_cache_metadata(
        source_table="tennis.gold_match_features_asof",
        columns=("match_date", "rank_log_diff"),
        filters={"start_date": date(2024, 1, 1), "limit": None},
        snapshot={
            "row_count": 1,
            "min_match_date": "2024-01-01",
            "max_match_date": "2024-01-01",
            "max_feature_asof_date": "2023-12-31",
        },
    )

    write_feature_cache(frame, cache_path=cache_path, metadata=metadata)

    cached = load_feature_cache(cache_path, expected_metadata=metadata)
    assert cached is not None
    assert cached.loc[0, "rank_log_diff"] == 0.42
    assert feature_cache_metadata_path(cache_path).exists()


def test_feature_cache_rejects_stale_metadata(tmp_path: Path) -> None:
    cache_path = tmp_path / "features.parquet"
    frame = pd.DataFrame({"match_date": [date(2024, 1, 1)], "rank_log_diff": [0.42]})
    metadata = feature_cache_metadata(
        source_table="tennis.gold_match_features_asof",
        columns=("match_date", "rank_log_diff"),
        filters={"start_date": date(2024, 1, 1), "limit": None},
        snapshot={
            "row_count": 1,
            "min_match_date": "2024-01-01",
            "max_match_date": "2024-01-01",
            "max_feature_asof_date": "2023-12-31",
        },
    )
    stale_metadata = {
        **metadata,
        "snapshot": {
            "row_count": 2,
            "min_match_date": "2024-01-01",
            "max_match_date": "2024-01-02",
            "max_feature_asof_date": "2024-01-01",
        },
    }

    write_feature_cache(frame, cache_path=cache_path, metadata=metadata)

    assert load_feature_cache(cache_path, expected_metadata=stale_metadata) is None
