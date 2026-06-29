from datetime import date

import pytest

from tennis_sabermetrics.evaluation.temporal_split import TemporalSplit


def test_temporal_split_labels_dates() -> None:
    split = TemporalSplit(
        train_start=date(2010, 1, 1),
        train_end=date(2019, 12, 31),
        validation_start=date(2020, 1, 1),
        validation_end=date(2021, 12, 31),
        test_start=date(2022, 1, 1),
        test_end=None,
    )

    split.validate()
    assert split.label_for_date(date(2018, 6, 1)) == "train"
    assert split.label_for_date(date(2020, 6, 1)) == "validation"
    assert split.label_for_date(date(2024, 6, 1)) == "test"


def test_temporal_split_rejects_overlap() -> None:
    split = TemporalSplit(
        train_start=None,
        train_end=date(2020, 1, 1),
        validation_start=date(2019, 1, 1),
        validation_end=date(2021, 1, 1),
        test_start=date(2022, 1, 1),
        test_end=None,
    )

    with pytest.raises(ValueError):
        split.validate()

