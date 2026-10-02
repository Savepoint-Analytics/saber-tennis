from pathlib import Path

import pandas as pd

from tennis_sabermetrics.ingest.warehouse import (
    count_source_file_rows,
    match_stats_landing_frame,
    matches_landing_frame,
    player_file_landing_frame,
    rankings_landing_frame,
)


def test_matches_landing_frame_normalizes_core_fields() -> None:
    frame = pd.DataFrame(
        {
            "_source_key": ["aneeshers_tennis_sackmann_archive"],
            "_tour": ["atp"],
            "_source_commit_sha": ["abc123"],
            "_snapshot_date": ["2026-08-25"],
            "tourney_id": ["2026-580"],
            "tourney_date": ["20260112"],
            "match_num": ["300"],
            "surface": ["Hard"],
            "round": ["F"],
            "best_of": ["5"],
            "winner_id": ["1001"],
            "loser_id": ["1002"],
            "score": ["6-4 6-4"],
            "minutes": ["98"],
        }
    )

    landing = matches_landing_frame(frame)

    assert landing.loc[0, "match_id"] == "atp:2026-580:300"
    assert landing.loc[0, "tourney_date"].isoformat() == "2026-01-12"
    assert landing.loc[0, "best_of"] == 5


def test_rankings_landing_frame_uses_headerless_ranking_columns() -> None:
    frame = pd.DataFrame(
        {
            "0": ["20260105"],
            "1": ["1"],
            "2": ["1001"],
            "3": ["12000"],
            "_source_key": ["aneeshers_tennis_sackmann_archive"],
            "_tour": ["wta"],
            "_source_commit_sha": ["abc123"],
            "_snapshot_date": ["2026-08-25"],
        }
    )

    landing = rankings_landing_frame(frame)

    assert landing.loc[0, "ranking_date"].isoformat() == "2026-01-05"
    assert landing.loc[0, "rank"] == 1
    assert landing.loc[0, "ranking_points"] == 12000


def test_match_stats_landing_frame_creates_winner_and_loser_rows() -> None:
    frame = pd.DataFrame(
        {
            "_source_key": ["aneeshers_tennis_sackmann_archive"],
            "_tour": ["atp"],
            "_source_commit_sha": ["abc123"],
            "_snapshot_date": ["2026-08-25"],
            "tourney_id": ["2026-580"],
            "match_num": ["300"],
            "winner_id": ["1001"],
            "loser_id": ["1002"],
            "w_ace": ["10"],
            "w_df": ["2"],
            "w_svpt": ["80"],
            "w_1stIn": ["50"],
            "w_1stWon": ["40"],
            "w_2ndWon": ["18"],
            "w_bpSaved": ["4"],
            "w_bpFaced": ["5"],
            "l_ace": ["5"],
            "l_df": ["4"],
            "l_svpt": ["75"],
            "l_1stIn": ["45"],
            "l_1stWon": ["30"],
            "l_2ndWon": ["12"],
            "l_bpSaved": ["6"],
            "l_bpFaced": ["10"],
        }
    )

    landing = match_stats_landing_frame(frame)

    assert len(landing) == 2
    winner = landing[landing["is_winner"]].iloc[0]
    loser = landing[~landing["is_winner"]].iloc[0]
    assert winner["second_serve_points_total"] == 30
    assert loser["second_serve_points_total"] == 30


def test_player_file_landing_frame_uses_player_source_file() -> None:
    frame = pd.DataFrame(
        {
            "_source_key": ["aneeshers_tennis_sackmann_archive"],
            "_tour": ["atp"],
            "_source_commit_sha": ["abc123"],
            "_snapshot_date": ["2026-08-25"],
            "player_id": ["1001"],
            "name_first": ["Alice"],
            "name_last": ["Alpha"],
            "hand": ["R"],
            "dob": ["20000131"],
            "ioc": ["USA"],
            "height": ["170"],
        }
    )

    landing = player_file_landing_frame(frame)

    assert landing.loc[0, "name_first"] == "Alice"
    assert landing.loc[0, "dob"].isoformat() == "2000-01-31"
    assert landing.loc[0, "height_cm"] == 170


def test_count_source_file_rows_handles_headered_and_headerless_csv(tmp_path: Path) -> None:
    matches = tmp_path / "atp_matches_2026.csv"
    rankings = tmp_path / "atp_rankings_current.csv"
    readme = tmp_path / "README.md"
    matches.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    rankings.write_text("20260101,1,1001,12000\n20260108,1,1001,11800\n", encoding="utf-8")
    readme.write_text("not tabular\n", encoding="utf-8")

    assert count_source_file_rows(matches) == 2
    assert count_source_file_rows(rankings) == 2
    assert count_source_file_rows(readme) is None
