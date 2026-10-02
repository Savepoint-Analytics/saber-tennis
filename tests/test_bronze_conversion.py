from datetime import date

import pandas as pd

from tennis_sabermetrics.ingest.bronze import (
    BronzeMetadata,
    build_bronze_for_source,
    convert_csv_to_bronze_parquet,
    validate_bronze_schema,
)


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


def test_convert_csv_to_bronze_parquet_handles_mixed_source_columns(tmp_path) -> None:
    csv_path = tmp_path / "matches.csv"
    parquet_path = tmp_path / "bronze" / "matches.parquet"
    csv_path.write_text("draw_size,winner_id\n32,A\nR,B\n", encoding="utf-8")

    metadata = BronzeMetadata.from_source(
        source_key="aneeshers_tennis_sackmann_archive",
        source_url="https://github.com/Aneeshers/tennis-sackmann-archive",
        source_commit_sha="archive123",
        snapshot_date=date(2026, 8, 25),
        license_name="CC BY-NC-SA 4.0",
        tour="atp",
    )

    row_count = convert_csv_to_bronze_parquet(csv_path, parquet_path, metadata)
    frame = pd.read_parquet(parquet_path)

    assert row_count == 2
    assert frame["draw_size"].tolist() == ["32", "R"]
    assert frame.loc[0, "_tour"] == "atp"


def test_build_bronze_for_atp_match_and_ranking_csvs(tmp_path) -> None:
    source_root = tmp_path / "tennis_atp"
    bronze_root = tmp_path / "bronze"
    source_root.mkdir()
    (source_root / "atp_matches_2026.csv").write_text(
        "winner_id,loser_id\nA,B\n",
        encoding="utf-8",
    )
    (source_root / "atp_rankings_2026.csv").write_text(
        "20260101,1,A,1000\n",
        encoding="utf-8",
    )
    (source_root / "atp_players.csv").write_text(
        "player_id,name_first,name_last,hand,dob,ioc,height\nA,Alice,Alpha,R,20000101,USA,170\n",
        encoding="utf-8",
    )

    results = build_bronze_for_source(
        source_key="jeffsackmann_tennis_atp",
        snapshot_date=date(2026, 7, 15),
        source_root=source_root,
        bronze_root=bronze_root,
        source_commit_sha="abc123",
    )

    assert {result.table_name for result in results} == {"players", "matches", "rankings"}
    assert all(result.parquet_path.exists() for result in results)
    match_result = next(result for result in results if result.table_name == "matches")
    match_frame = pd.read_parquet(match_result.parquet_path)
    assert match_frame.loc[0, "_source_key"] == "jeffsackmann_tennis_atp"


def test_build_bronze_for_fallback_archive_tour(tmp_path) -> None:
    source_root = tmp_path / "tennis-sackmann-archive"
    atp_root = source_root / "atp"
    bronze_root = tmp_path / "bronze"
    atp_root.mkdir(parents=True)
    (atp_root / "atp_matches_2026.csv").write_text(
        "winner_id,loser_id\nA,B\n",
        encoding="utf-8",
    )
    (atp_root / "atp_rankings_2026.csv").write_text(
        "20260101,1,A,1000\n",
        encoding="utf-8",
    )
    (atp_root / "atp_players.csv").write_text(
        "player_id,name_first,name_last,hand,dob,ioc,height\nA,Alice,Alpha,R,20000101,USA,170\n",
        encoding="utf-8",
    )

    results = build_bronze_for_source(
        source_key="aneeshers_tennis_sackmann_archive",
        archive_tour="atp",
        snapshot_date=date(2026, 8, 24),
        source_root=source_root,
        bronze_root=bronze_root,
        source_commit_sha="archive123",
    )

    assert {result.table_name for result in results} == {"players", "matches", "rankings"}
    match_result = next(result for result in results if result.table_name == "matches")
    match_frame = pd.read_parquet(match_result.parquet_path)
    assert match_frame.loc[0, "_source_key"] == "aneeshers_tennis_sackmann_archive"
    assert match_frame.loc[0, "_source_url"] == "https://github.com/Aneeshers/tennis-sackmann-archive"
    assert match_frame.loc[0, "_tour"] == "atp"
    assert "/aneeshers_tennis_sackmann_archive/atp/matches/" in str(match_result.parquet_path)


def test_validate_bronze_schema_accepts_valid_match_parquet(tmp_path) -> None:
    csv_path = tmp_path / "atp_matches_2026.csv"
    parquet_path = tmp_path / "bronze" / "atp_matches_2026.parquet"
    csv_path.write_text(
        "tourney_id,tourney_date,match_num,winner_id,loser_id,score\n"
        "2026-580,20260112,300,A,B,6-4 6-4\n",
        encoding="utf-8",
    )
    metadata = BronzeMetadata.from_source(
        source_key="aneeshers_tennis_sackmann_archive",
        source_url="https://github.com/Aneeshers/tennis-sackmann-archive",
        source_commit_sha="archive123",
        snapshot_date=date(2026, 8, 25),
        license_name="CC BY-NC-SA 4.0",
        tour="atp",
    )

    convert_csv_to_bronze_parquet(csv_path, parquet_path, metadata)
    result = validate_bronze_schema(parquet_path, table_name="matches")

    assert result.is_valid


def test_validate_bronze_schema_flags_bad_date(tmp_path) -> None:
    csv_path = tmp_path / "atp_matches_2026.csv"
    parquet_path = tmp_path / "bronze" / "atp_matches_2026.parquet"
    csv_path.write_text(
        "tourney_id,tourney_date,match_num,winner_id,loser_id,score\n"
        "2026-580,not-a-date,300,A,B,6-4 6-4\n",
        encoding="utf-8",
    )
    metadata = BronzeMetadata.from_source(
        source_key="aneeshers_tennis_sackmann_archive",
        source_url="https://github.com/Aneeshers/tennis-sackmann-archive",
        source_commit_sha="archive123",
        snapshot_date=date(2026, 8, 25),
        license_name="CC BY-NC-SA 4.0",
        tour="atp",
    )

    convert_csv_to_bronze_parquet(csv_path, parquet_path, metadata)
    result = validate_bronze_schema(parquet_path, table_name="matches")

    assert not result.is_valid
    assert result.unparseable_date_columns == ("tourney_date",)
