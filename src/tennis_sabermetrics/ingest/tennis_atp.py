"""ATP source-specific ingestion hooks."""

from __future__ import annotations

from pathlib import Path

DEFAULT_SOURCE_KEY = "jeffsackmann_tennis_atp"


def iter_atp_match_csvs(source_root: Path) -> list[Path]:
    return sorted(source_root.glob("atp_matches_*.csv"))


def iter_atp_ranking_csvs(source_root: Path) -> list[Path]:
    return sorted(source_root.glob("atp_rankings_*.csv"))


def iter_atp_player_csvs(source_root: Path) -> list[Path]:
    return sorted(source_root.glob("atp_players.csv"))
