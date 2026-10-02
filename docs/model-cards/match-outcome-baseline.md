# Model Card: Match Outcome Baseline

Last updated: 2026-09-09.

Status: draft, non-commercial research/portfolio artifact. Not betting advice.

## Intended Use

This baseline estimates pre-match win probability for oriented ATP/WTA singles matches and supports the draft article [Why Elo And Serve/Return Context Beat Raw Rankings](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/articles/why-elo-serve-return-beat-rankings.md).

Appropriate uses:

- Explain why opponent-adjusted Elo and serve/return context outperform raw ranking difference.
- Compare simple transparent baselines under temporal and walk-forward validation.
- Produce non-commercial methodology, portfolio, and research artifacts with attribution.

Out-of-scope uses:

- Gambling advice, betting picks, or wagering products.
- Paid Savepoint Analytics deliverables from CC BY-NC-SA data without written permission or a commercial data source.
- Live production forecasts without source, identity, missingness, and calibration monitoring.

## Data

Feature table: `tennis.gold_match_features_asof`.

Current snapshot: 2026-08-25.

Current match coverage: 1990-01-01 to 2026-06-02.

Rows: 1,538,042.

Primary source key in current warehouse build: `aneeshers_tennis_sackmann_archive`, used as a reviewed fallback for Jeff Sackmann / Tennis Abstract ATP/WTA data. Treat the data as Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International unless source-specific license metadata says otherwise.

Required attribution:

> Data derived from Jeff Sackmann / Tennis Abstract repositories and/or The Tennis Abstract Match Charting Project. Original sources are licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International unless otherwise stated. This project is non-commercial research/portfolio work and does not redistribute raw third-party data.

## Prediction Target

Target column: `player_a_won`.

Rows are oriented by a stable hash of source, tour, match, tournament, and match date. The model does not use winner-vs-loser orientation as an input.

## Features

The logistic baseline uses:

- `rank_log_diff`
- `overall_elo_diff`
- `surface_elo_diff`
- `prior_win_pct_diff`
- `recent_10_win_pct_diff`
- `rest_days_diff`
- `serve_points_won_pct_diff`
- `return_points_won_pct_diff`

Every feature is designed to be known before the match date. Ranking, Elo, form, rest, and serve/return features are snapshotted before same-day match outcomes are incorporated.

## Validation

Default temporal split:

| Split | Date range |
|---|---|
| Train | 1990-01-01 to 2018-12-31 |
| Validation | 2019-01-01 to 2021-12-31 |
| Test | 2022-01-01 onward |

Walk-forward validation uses expanding train windows, three-year validation windows, and one-year test windows from 2016 through 2025.

Calibration methods:

- Platt scaling is fit on validation rows only and evaluated on test rows only.
- Isotonic calibration is fit on validation rows only and evaluated on test rows only.

## Current Held-Out Results

2022-onward test period, 287,324 matches:

| Model | Log loss | Brier | ROC-AUC | Accuracy |
|---|---:|---:|---:|---:|
| Logistic baseline | 0.586271 | 0.200775 | 0.755743 | 0.687172 |
| Logistic baseline Platt | 0.586288 | 0.200792 | 0.755743 | 0.687193 |
| Logistic baseline isotonic | 0.586358 | 0.200832 | 0.755604 | 0.687144 |
| Overall Elo Platt | 0.594403 | 0.203944 | 0.747738 | 0.682418 |
| Overall Elo | 0.594455 | 0.203916 | 0.747738 | 0.682386 |
| Surface Elo isotonic | 0.600412 | 0.206687 | 0.739998 | 0.675986 |
| Surface Elo Platt | 0.600509 | 0.206690 | 0.740134 | 0.675850 |
| Surface Elo | 0.600943 | 0.206915 | 0.740134 | 0.675868 |
| Ranking log difference isotonic | 0.645282 | 0.227019 | 0.671386 | 0.614849 |
| Ranking log difference | 0.646413 | 0.227228 | 0.671500 | 0.614822 |
| Ranking log difference Platt | 0.646679 | 0.227515 | 0.671500 | 0.614933 |

Uncalibrated logistic has the best held-out log loss. Isotonic improves the ranking-only baseline and has the smallest logistic calibration-bin tail error, while Platt remains slightly better than isotonic on logistic held-out log loss.

## Guardrails

Implemented checks:

- No random train/test splits.
- Feature as-of dates must be before match date.
- Oriented feature rows must be unique.
- `player_a_id` and `player_b_id` must differ.
- Difference columns must match player A minus player B input columns.
- Calibrated models are reported on held-out test rows only.
- Diagnostics separate event level, draw stage, ranking population, and source coverage.

Current warehouse verification:

- Future-feature violations: 0.
- Self-match rows: 0.
- `tournament_level` rows: 1,538,042.
- `draw_size` rows: 1,538,042.

## Known Limitations

- Current source coverage is dominated by a fallback archive source and inherits non-commercial licensing restrictions.
- Missing-rank segments with high performance are source- and event-mix findings, not broad model claims.
- `tournament_level` and qualifying/main-draw flags are coarse source-derived labels; see [event-level-mapping.md](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/methodology/event-level-mapping.md).
- Serve/return feature availability is uneven across eras, tours, and event classes.
- No legally reviewed betting odds baseline is loaded.
- Player identity normalization is still source-ID based.
