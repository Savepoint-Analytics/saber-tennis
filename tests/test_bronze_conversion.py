from datetime import date

import pandas as pd

from tennis_sabermetrics.ingest.bronze import BronzeMetadata, convert_csv_to_bronze_parquet


def test_convert_csv_to_bronze_parquet_adds_metadata(tmp_path) -> None:
    csv_path = tmp_path / "matches.csv"
    parquet_path = tmp_path / "bronze" / "matches.parquet"
    csv_path.write_text("winner_id,loser_id\nA,B\n", encoding="utf-8")

    metadata = BronzeMetadata.from_source(
        source_key="jeffsackmann_tennis_atp",
        source_url="https://github.com/JeffSackmann/tennis_atp",
        source_commit_sha="abc123",
        snapshot_date=date(2026, 7, 8),
        license_name="CC BY-NC-SA 4.0",
    )

    row_count = convert_csv_to_bronze_parquet(csv_path, parquet_path, metadata)
    frame = pd.read_parquet(parquet_path)

    assert row_count == 1
    assert frame.loc[0, "_source_key"] == "jeffsackmann_tennis_atp"
    assert frame.loc[0, "_source_commit_sha"] == "abc123"
    assert frame.loc[0, "_snapshot_date"] == "2026-07-08"

