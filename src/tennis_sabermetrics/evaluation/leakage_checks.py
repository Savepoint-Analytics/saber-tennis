"""Small leakage guardrails used by feature builders and tests."""

from __future__ import annotations

from datetime import date


def assert_feature_asof_date(feature_asof_date: date, match_date: date) -> None:
    if feature_asof_date >= match_date:
        raise ValueError(
            f"Feature as-of date {feature_asof_date.isoformat()} must be before "
            f"match date {match_date.isoformat()}"
        )

