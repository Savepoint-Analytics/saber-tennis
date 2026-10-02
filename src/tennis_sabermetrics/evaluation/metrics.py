"""Evaluation metrics for match probability models."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn import metrics as sk_metrics  # type: ignore[import-untyped]

MATCH_PROBABILITY_METRICS = (
    "log_loss",
    "brier_score",
    "roc_auc",
    "calibration_curve",
    "accuracy_secondary",
)


@dataclass(frozen=True)
class ProbabilityMetrics:
    log_loss: float
    brier_score: float
    roc_auc: float | None
    accuracy: float
    sample_size: int


def evaluate_binary_probabilities(y_true: list[bool] | np.ndarray, y_probability: np.ndarray) -> ProbabilityMetrics:
    """Evaluate binary probability predictions with project-required metrics."""

    y_array = np.asarray(y_true, dtype=int)
    p_array = np.clip(np.asarray(y_probability, dtype=float), 1e-6, 1 - 1e-6)
    roc_auc = None
    if len(np.unique(y_array)) == 2:
        roc_auc = float(sk_metrics.roc_auc_score(y_array, p_array))
    return ProbabilityMetrics(
        log_loss=float(sk_metrics.log_loss(y_array, p_array, labels=[0, 1])),
        brier_score=float(sk_metrics.brier_score_loss(y_array, p_array)),
        roc_auc=roc_auc,
        accuracy=float(sk_metrics.accuracy_score(y_array, p_array >= 0.5)),
        sample_size=len(y_array),
    )
