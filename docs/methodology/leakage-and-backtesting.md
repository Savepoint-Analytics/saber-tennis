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

## What A Leakage Test Means

A leakage test is a test that proves the model input table does not contain information from the future.

In this project, examples include:

- Assert every feature row has `max_feature_asof_date < match_date`.
- Assert ranking features use a ranking date before the match date, not the same day or after.
- Assert Elo values are captured before applying the current match result.
- Assert rolling form windows exclude the current match.
- Assert a join creates exactly one feature row per match, instead of duplicating matches through many-to-many joins.

Without these tests, a model can look accurate because it accidentally learned from information that would not have existed before the match. That is the core failure mode the third next step is meant to prevent.

## Implemented Gates

The baseline evaluator now fails before model evaluation if the gold feature table violates any of these checks:

- `feature_row_id` uniqueness.
- Unique oriented match-feature grain: source, tour, match, tournament, date, player A, player B.
- Distinct `player_a_id` and `player_b_id`.
- `max_feature_asof_date`, `player_a_rank_asof_date`, and `player_b_rank_asof_date` before `match_date`.
- Rank values and rank as-of dates present or absent together.
- Non-negative rest-day features.
- Difference columns matching their source inputs, including rank, rank-log, Elo, surface Elo, prior win rate, recent form, rest, serve, and return differences.

The same core checks are also available as dbt singular tests over `tennis.gold_match_features_asof`.
