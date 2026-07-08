"""WTA source-specific ingestion hooks."""

from __future__ import annotations

from pathlib import Path

DEFAULT_SOURCE_KEY = "jeffsackmann_tennis_wta"


def iter_wta_match_csvs(source_root: Path) -> list[Path]:
    return sorted(source_root.glob("wta_matches_*.csv"))


def iter_wta_ranking_csvs(source_root: Path) -> list[Path]:
    return sorted(source_root.glob("wta_rankings_*.csv"))
