"""Player normalization helpers."""

from __future__ import annotations


def normalized_player_key(source_key: str, player_id: str | int) -> str:
    return f"{source_key}:{player_id}".strip().lower()

