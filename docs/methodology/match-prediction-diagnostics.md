# Match Prediction Diagnostics

Diagnostics extend the baseline evaluation with calibration, missingness, and segmented performance checks.

Run command:

```bash
uv run tennis-sabermetrics evaluate-match-diagnostics \
  --output-dir outputs/tables \
  --calibration-plot-path outputs/charts/match_prediction_calibration.html \
  --fail-on-unmapped-events
```

The command writes:

- `outputs/tables/match_prediction_calibration.csv`
- `outputs/tables/match_feature_missingness.csv`
- `outputs/tables/match_segment_backtests.csv`
- `outputs/tables/match_source_composition_diagnostics.csv`
- `outputs/tables/match_event_level_mapping.csv`
- `outputs/charts/match_prediction_calibration.html`

It also persists:

- `tennis.gold_prediction_calibration`
- `tennis.gold_feature_missingness`
- `tennis.gold_segment_backtests`
- `tennis.gold_source_composition_diagnostics`
- `tennis.gold_event_level_mapping_diagnostics`

The PostgreSQL path first runs SQL leakage checks, then loads a narrow diagnostics feature frame instead of the full gold table. The current uncached hard-gated refresh completed in 113.45 seconds on the local environment; a cached repeat with PostgreSQL persistence skipped completed in 77.26 seconds. Use `--fail-on-unmapped-events` before publication to turn unmapped tournament codes into a hard failure; otherwise the CLI emits a warning and writes the mapping report.

By default, the narrow feature extract is cached at `outputs/cache/match_diagnostic_features.parquet` with adjacent JSON metadata. The cache is reused only when the selected columns, date filters, limit, and lightweight source-table snapshot match. Use `--no-feature-cache` to force a fresh PostgreSQL read, or `--feature-cache-path` to put the local cache somewhere else.

## Current Result Counts

Last refreshed on 2026-09-09:

| Output | Rows |
|---|---:|
| Calibration bins | 160 |
| Missingness rows | 648 |
| Segment backtest rows | 1,164 |
| Source-composition rows | 159 |
| Event-level mapping rows | 38 |

The current hard-gated refresh has `unmapped_event_rows = 0`.

## Calibration

Calibration compares predicted probabilities with observed win rates inside probability buckets.

Worst uncalibrated logistic-baseline test bins by absolute calibration error:

| Bin | Sample size | Mean predicted | Observed win rate | Error |
|---:|---:|---:|---:|---:|
| 9 | 7,490 | 0.9314 | 0.9123 | -0.0191 |
| 0 | 7,530 | 0.0684 | 0.0869 | 0.0184 |
| 2 | 31,357 | 0.2524 | 0.2421 | -0.0103 |
| 7 | 31,162 | 0.7475 | 0.7568 | 0.0093 |
| 6 | 39,336 | 0.6485 | 0.6563 | 0.0078 |

Hash-based player orientation removed the prior side-assignment calibration artifact. The current logistic baseline's largest test-bin calibration errors are roughly 1-2 percentage points and concentrated in the tails. Platt and isotonic calibration are fit on validation rows only and persisted for test rows only. Isotonic has the smallest worst-bin logistic calibration error, while the uncalibrated logistic baseline keeps the best held-out log loss.

## Missingness

Missingness is summarized by tour, surface, era, stat availability, and feature name.

The highest missingness is concentrated in serve/return features for segments with `no_serve_return` stat availability. This is expected because source match statistics are incomplete across eras, tours, and competition levels. Ranking and Elo features remain broadly available, while serve/return components require explicit missingness caveats in public outputs.

## Segmented Backtests

Segmented backtests report model metrics by:

- Tour.
- Surface.
- Match format.
- Event level.
- Qualifying/main draw stage.
- Era.
- Ranking coverage.
- Ranking population.
- Source coverage.

See [event-level-mapping.md](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/methodology/event-level-mapping.md) for the source-specific tournament code mapping used by these flags.

Largest 2022+ logistic-baseline test segments:

| Tour | Surface | Format | Event | Draw | Ranking coverage | Source coverage | N | Log loss | ROC-AUC |
|---|---|---|---|---|---|---|---:|---:|---:|
| ATP | hard | best_of_3 | itf_level | main_draw | both_ranked | fallback_archive | 35,079 | 0.5934 | 0.7497 |
| WTA | hard | best_of_3 | itf_level | main_draw | both_ranked | fallback_archive | 34,021 | 0.5907 | 0.7496 |
| ATP | clay | best_of_3 | itf_level | main_draw | both_ranked | fallback_archive | 28,645 | 0.5883 | 0.7568 |
| WTA | clay | best_of_3 | itf_level | main_draw | both_ranked | fallback_archive | 26,694 | 0.5912 | 0.7502 |
| WTA | hard | best_of_3 | itf_level | qualifying | missing_rank | fallback_archive | 15,899 | 0.5529 | 0.8000 |
| WTA | clay | best_of_3 | itf_level | qualifying | missing_rank | fallback_archive | 15,401 | 0.5511 | 0.8034 |

Segment metrics are diagnostic, not final model claims. Some missing-rank segments score well because the current feature set still contains Elo/form signals; source-level composition must be reviewed before publication.

## Source Composition

Source-composition diagnostics summarize each evaluation segment by source key, source share, date range, serve/return availability, ranking coverage, and logistic metrics.

Top missing-rank 2020s test source segments by ROC-AUC:

| Tour | Surface | Format | Event | Draw | Source coverage | Source | N | Source share | Serve/return availability | Log loss | ROC-AUC |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| ATP | clay | best_of_3 | challenger_level | qualifying | fallback_archive | `aneeshers_tennis_sackmann_archive` | 369 | 1.000 | 0.534 | 0.3357 | 0.9303 |
| ATP | hard | best_of_3 | challenger_level | qualifying | fallback_archive | `aneeshers_tennis_sackmann_archive` | 330 | 1.000 | 0.533 | 0.4129 | 0.8914 |
| WTA | carpet | best_of_3 | itf_level | main_draw | fallback_archive | `aneeshers_tennis_sackmann_archive` | 271 | 1.000 | 0.210 | 0.4635 | 0.8717 |
| WTA | hard | best_of_3 | itf_level | main_draw | fallback_archive | `aneeshers_tennis_sackmann_archive` | 9,221 | 1.000 | 0.239 | 0.5156 | 0.8310 |
| WTA | clay | best_of_3 | itf_level | main_draw | fallback_archive | `aneeshers_tennis_sackmann_archive` | 6,894 | 1.000 | 0.207 | 0.5209 | 0.8250 |

Because these high-performing missing-rank segments are currently 100% from the fallback archive source, they should be treated as source-composition findings rather than broad model-performance claims.
