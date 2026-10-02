# Match Prediction Baselines

This project now has a first baseline match-outcome evaluation over `tennis.gold_match_features_asof`.

Run command:

```bash
uv run tennis-sabermetrics evaluate-match-baselines \
  --output-path outputs/tables/match_baseline_evaluation.csv
```

The command also writes rows to `tennis.gold_prediction_backtests` unless `--no-persist-postgres` is set.

By default, the PostgreSQL path reuses a snapshot-aware feature cache at `outputs/cache/match_baseline_features.parquet`. Use `--no-feature-cache` to force a fresh warehouse read, or `--feature-cache-path` to choose another local cache file. The current cache-populating no-persist baseline refresh completed in 307.73 seconds on the local environment.

Walk-forward command:

```bash
uv run tennis-sabermetrics evaluate-match-walk-forward \
  --first-test-year 2016 \
  --last-test-year 2025 \
  --validation-years 3 \
  --output-path outputs/tables/match_walk_forward_evaluation.csv
```

The walk-forward command writes rows to `tennis.gold_prediction_walk_forward_backtests` unless `--no-persist-postgres` is set. The PostgreSQL path first runs SQL leakage gates, then loads a narrow model-ready feature frame for faster annual evaluation. It reuses `outputs/cache/match_walk_forward_features.parquet` by default, with the same `--no-feature-cache` and `--feature-cache-path` controls. The current cache-populating no-persist walk-forward refresh completed in 85.30 seconds on the local environment.

Before any model is evaluated, the command runs leakage checks against `tennis.gold_match_features_asof`. Evaluation fails if feature dates are not before match date, if joins duplicate the oriented match grain, if a row compares a player with themselves, or if difference columns no longer match the joined player-level inputs.

## Split

Current default temporal split:

| Split | Date range |
|---|---|
| Train | 1990-01-01 to 2018-12-31 |
| Validation | 2019-01-01 to 2021-12-31 |
| Test | 2022-01-01 onward |

Random train/test splits are not valid for this project because they let future-era patterns influence past-era evaluation.

## Models

| Model | Definition |
|---|---|
| `ranking_log_difference` | Logistic transform of log player-rank ratio. |
| `overall_elo` | Elo probability from pre-match overall Elo difference. |
| `surface_elo` | Elo probability from pre-match blended surface Elo difference. |
| `logistic_baseline` | Scikit-learn logistic regression over ranking, Elo, form, rest, and serve/return difference features. |
| `*_platt` | Validation-fitted Platt calibration of each base probability model. Evaluated on test only. |
| `*_isotonic` | Validation-fitted isotonic calibration of each base probability model. Evaluated on test only. |

## Current Results

Validation period: 2019-01-01 to 2021-12-31, 128,708 matches.

| Model | Log loss | Brier | ROC-AUC | Accuracy |
|---|---:|---:|---:|---:|
| Ranking log difference | 0.656070 | 0.231711 | 0.653488 | 0.602581 |
| Overall Elo | 0.600568 | 0.206988 | 0.738619 | 0.672227 |
| Blended surface Elo | 0.607804 | 0.210057 | 0.730881 | 0.667177 |
| Logistic baseline | 0.593800 | 0.204140 | 0.746440 | 0.678171 |

Test period: 2022-01-01 onward, 287,324 matches.

| Model | Log loss | Brier | ROC-AUC | Accuracy |
|---|---:|---:|---:|---:|
| Ranking log difference | 0.646413 | 0.227228 | 0.671500 | 0.614822 |
| Overall Elo | 0.594455 | 0.203916 | 0.747738 | 0.682386 |
| Blended surface Elo | 0.600943 | 0.206915 | 0.740134 | 0.675868 |
| Logistic baseline | 0.586271 | 0.200775 | 0.755743 | 0.687172 |
| Ranking log difference Platt | 0.646679 | 0.227515 | 0.671500 | 0.614933 |
| Overall Elo Platt | 0.594403 | 0.203944 | 0.747738 | 0.682418 |
| Blended surface Elo Platt | 0.600509 | 0.206690 | 0.740134 | 0.675850 |
| Logistic baseline Platt | 0.586288 | 0.200792 | 0.755743 | 0.687193 |
| Ranking log difference isotonic | 0.645282 | 0.227019 | 0.671386 | 0.614849 |
| Overall Elo isotonic | 0.595021 | 0.203981 | 0.747580 | 0.682042 |
| Blended surface Elo isotonic | 0.600412 | 0.206687 | 0.739998 | 0.675986 |
| Logistic baseline isotonic | 0.586358 | 0.200832 | 0.755604 | 0.687144 |

## Interpretation

Overall Elo remains a strong transparent baseline. Blended surface Elo improves on the prior independent surface Elo because sparse surfaces borrow from overall player strength instead of resetting to 1500. The logistic model has the best current test log loss and ROC-AUC.

Platt and isotonic calibration are fit on the validation split, so calibrated metrics are reported on the test split only. Isotonic improves the raw ranking baseline and has the smallest worst-bin logistic calibration error, but neither calibration method improves logistic held-out log loss.

## Walk-Forward Results

The 2016-2025 walk-forward evaluation uses expanding training windows, three-year validation windows, and one-year test windows. It currently persists 120 test rows across 550,657 annual test matches.

The current narrow-loader implementation completed the full PostgreSQL-backed 2016-2025 refresh in 74.29 seconds on the local environment, down from 141.66 seconds before the wide feature-frame load was removed.

| Model | Windows | Avg log loss | Avg Brier | Avg ROC-AUC | Avg accuracy |
|---|---:|---:|---:|---:|---:|
| Logistic baseline | 10 | 0.586946 | 0.201187 | 0.754366 | 0.685356 |
| Logistic baseline Platt | 10 | 0.586974 | 0.201198 | 0.754366 | 0.685470 |
| Logistic baseline isotonic | 10 | 0.587070 | 0.201232 | 0.754248 | 0.685216 |
| Overall Elo isotonic | 10 | 0.594287 | 0.204161 | 0.746673 | 0.680093 |
| Overall Elo Platt | 10 | 0.594388 | 0.204133 | 0.746775 | 0.680216 |
| Overall Elo | 10 | 0.594394 | 0.204121 | 0.746775 | 0.680254 |
| Blended surface Elo isotonic | 10 | 0.601065 | 0.207093 | 0.738666 | 0.674328 |
| Blended surface Elo Platt | 10 | 0.601252 | 0.207089 | 0.738765 | 0.674071 |
| Blended surface Elo | 10 | 0.601479 | 0.207252 | 0.738765 | 0.674004 |
| Ranking log difference isotonic | 10 | 0.644950 | 0.226846 | 0.671655 | 0.616270 |
| Ranking log difference | 10 | 0.646298 | 0.227138 | 0.671815 | 0.616726 |
| Ranking log difference Platt | 10 | 0.646309 | 0.227153 | 0.671815 | 0.616551 |

The ranking of baseline approaches is stable: logistic features outperform overall Elo, overall Elo outperforms blended surface Elo alone, and all Elo-based approaches outperform raw ranking difference.

These results are for non-commercial research and are not gambling advice.

See [match-prediction-diagnostics.md](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/methodology/match-prediction-diagnostics.md) for calibration, missingness, and segment-level backtest outputs.
