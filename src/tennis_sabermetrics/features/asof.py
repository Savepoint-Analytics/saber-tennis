"""As-of-date feature utilities."""

from __future__ import annotations

from datetime import date

from tennis_sabermetrics.evaluation.leakage_checks import assert_feature_asof_date


def validate_asof_feature(feature_name: str, feature_asof_date: date, match_date: date) -> str:
    assert_feature_asof_date(feature_asof_date, match_date)
    return feature_name

