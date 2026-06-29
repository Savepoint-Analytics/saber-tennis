"""Temporal split helpers for leakage-resistant match prediction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class TemporalSplit:
    train_start: date | None
    train_end: date
    validation_start: date
    validation_end: date
    test_start: date
    test_end: date | None

    def label_for_date(self, match_date: date) -> str:
        if self.train_start is not None and match_date < self.train_start:
            return "excluded"
        if match_date <= self.train_end:
            return "train"
        if self.validation_start <= match_date <= self.validation_end:
            return "validation"
        if self.test_start <= match_date and (self.test_end is None or match_date <= self.test_end):
            return "test"
        return "excluded"

    def validate(self) -> None:
        if not (self.train_end < self.validation_start <= self.validation_end < self.test_start):
            raise ValueError("Temporal split windows must be ordered and non-overlapping")

