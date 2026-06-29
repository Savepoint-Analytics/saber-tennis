# Leakage And Backtesting

Tennis prediction is highly vulnerable to future information leakage. Any pre-match feature must be known before the match starts.

## Forbidden In Pre-Match Features

- Match result.
- Final score-derived stats.
- Post-match ranking updates.
- Post-match Elo updates.
- Tournament round reached after the match.
- Season-end or future rolling averages.
- Opponent form that includes the current or future match.

## Default Validation

Use temporal splits or walk-forward validation. Random row splits are invalid for match prediction.

Minimum probability metrics:

- Log loss.
- Brier score.
- ROC-AUC.
- Calibration curve.
- Accuracy only as a secondary metric.

## Baselines

Always compare predictive models against:

1. Official ranking difference.
2. Overall Elo.
3. Surface Elo.
4. Serve/return component model.
5. Betting odds only if legally available and isolated from public outputs.

