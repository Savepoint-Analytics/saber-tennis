from datetime import date

import pytest

from tennis_sabermetrics.features.asof import validate_asof_feature


def test_asof_feature_must_precede_match_date() -> None:
    assert (
        validate_asof_feature("elo_rating", date(2024, 1, 1), date(2024, 1, 2))
        == "elo_rating"
    )

    with pytest.raises(ValueError):
        validate_asof_feature("elo_rating", date(2024, 1, 2), date(2024, 1, 2))

