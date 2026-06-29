"""Surface normalization."""

from __future__ import annotations


SURFACE_ALIASES = {
    "hard": "hard",
    "clay": "clay",
    "grass": "grass",
    "carpet": "carpet",
    "indoor hard": "indoor_hard",
}


def normalize_surface(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().lower().replace("-", " ")
    return SURFACE_ALIASES.get(cleaned, cleaned.replace(" ", "_"))

