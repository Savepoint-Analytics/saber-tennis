"""Match normalization helpers."""

from __future__ import annotations

from datetime import date


def match_key(source_key: str, tour: str, match_date: date, winner_id: str, loser_id: str) -> str:
    return f"{source_key}:{tour}:{match_date.isoformat()}:{winner_id}:{loser_id}".lower()

