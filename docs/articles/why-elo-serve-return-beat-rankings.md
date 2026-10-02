# Why Elo And Serve/Return Context Beat Raw Rankings

Raw tennis rankings are useful. They are also blunt. Rankings mix player strength with tour rules, schedule choices, point-defense timing, injury gaps, event eligibility, and surface mix. For match prediction, the better question is not only "Who is ranked higher?" It is "What did each player prove before this match, against whom, on which surface, and with what serve/return profile?"

Using the current Savepoint Analytics tennis warehouse, a transparent baseline built from pre-match Elo, blended surface Elo, recent form, rest, and serve/return differences beats raw ranking difference on both a 2022-onward holdout and 2016-2025 walk-forward validation.

This is non-commercial research using Tennis Abstract / Jeff Sackmann-derived data. It is not gambling advice.

## The Short Version

The current best transparent baseline is a logistic model over:

- Ranking log difference.
- Overall Elo difference.
- Blended surface Elo difference.
- Prior win-rate difference.
- Recent 10-match form difference.
- Rest-days difference.
- Prior serve-points-won difference.
- Prior return-points-won difference.

The model uses only features available before match date. Platt and isotonic calibration are fit on validation windows only and compared on held-out test windows only.

## 2022+ Holdout

The primary holdout covers 287,324 ATP/WTA matches from 2022-01-01 through the current 2026-06-02 snapshot endpoint.

![Horizontal bar chart of 2022-onward held-out log loss by model. Lower bars are better; the logistic baseline remains strongest, while Platt and isotonic variants are calibration checks fit only on validation rows.](../../outputs/charts/article/match_holdout_log_loss.svg)

Caption: 2022-onward held-out log loss by model. Lower is better. The uncalibrated logistic baseline has the best current holdout log loss, while calibration variants are useful checks rather than new primary models.

| Model | Log loss | Brier | ROC-AUC | Accuracy |
|---|---:|---:|---:|---:|
| Ranking log difference | 0.646413 | 0.227228 | 0.671500 | 0.614822 |
| Overall Elo | 0.594455 | 0.203916 | 0.747738 | 0.682386 |
| Blended surface Elo | 0.600943 | 0.206915 | 0.740134 | 0.675868 |
| Logistic baseline | 0.586271 | 0.200775 | 0.755743 | 0.687172 |
| Logistic baseline Platt | 0.586288 | 0.200792 | 0.755743 | 0.687193 |
| Logistic baseline isotonic | 0.586358 | 0.200832 | 0.755604 | 0.687144 |

Raw rankings still contain signal, but overall Elo is a large improvement because it adjusts for opponent strength. The full logistic baseline improves further by adding surface, form, rest, and serve/return context.

## Walk-Forward Check

A single holdout can flatter a model if the split happens to suit it. The walk-forward check uses expanding training windows, three-year validation windows, and one-year test windows from 2016 through 2025. Across 550,657 annual test rows, the model ordering remains stable.

![Line chart of annual test log loss from 2016 through 2025 for ranking difference, overall Elo, blended surface Elo, and logistic baseline. The logistic baseline is consistently the lowest line.](../../outputs/charts/article/match_walk_forward_log_loss.svg)

Caption: Annual walk-forward test log loss. Lower is better. The logistic baseline is consistently strongest, followed by overall Elo, blended surface Elo, and raw ranking difference.

| Model | Windows | Avg log loss | Avg Brier | Avg ROC-AUC | Avg accuracy |
|---|---:|---:|---:|---:|---:|
| Logistic baseline | 10 | 0.586946 | 0.201187 | 0.754366 | 0.685356 |
| Logistic baseline Platt | 10 | 0.586974 | 0.201198 | 0.754366 | 0.685470 |
| Logistic baseline isotonic | 10 | 0.587070 | 0.201232 | 0.754248 | 0.685216 |
| Overall Elo | 10 | 0.594394 | 0.204121 | 0.746775 | 0.680254 |
| Blended surface Elo | 10 | 0.601479 | 0.207252 | 0.738765 | 0.674004 |
| Ranking log difference | 10 | 0.646298 | 0.227138 | 0.671815 | 0.616726 |

Calibration does not overturn the main result. Isotonic helps the ranking-only baseline and tightens the worst logistic calibration-bin error, but the uncalibrated logistic baseline still has the best headline log loss.

## Why The Extra Context Helps

Elo is a cleaner match-strength baseline than ranking because it updates from wins and losses against opponent strength. A top-50 player who loses narrowly to top-10 players should not be treated the same as a top-50 player who built their record mostly against weaker fields.

Surface context matters because tennis is not one environment. Grass, clay, hard courts, and indoor conditions reward different skills. The model uses a blended surface Elo that shrinks sparse surface records toward overall Elo:

```text
surface_weight = surface_matches / (surface_matches + 12)
blended_surface_elo = surface_weight * raw_surface_elo + (1 - surface_weight) * overall_elo
```

That shrinkage keeps the model from overreacting to tiny grass or indoor samples while still preserving surface-specific signal when enough evidence exists.

Serve and return features add useful explanatory context, but their missingness is not random. They are better covered in modern periods and in some event classes. That is why the diagnostics separate missing-rank performance by event level, qualifying/main draw, ranking population, source coverage, and source key.

## Source-Composition Guardrail

Some missing-rank segments show very strong ROC-AUC. Those rows should be treated as diagnostics, not broad model claims. The current top high-performing missing-rank 2020s segments are entirely from the fallback archive source and are concentrated in ITF/challenger populations.

![Horizontal bar chart of the top 2020s missing-rank test segments by logistic ROC-AUC. Segments are labeled by tour, surface, event level, and draw stage; these results are source-composition diagnostics, not broad model claims.](../../outputs/charts/article/match_source_guardrail.svg)

Caption: Top missing-rank 2020s test segments by logistic ROC-AUC. These segments help identify where the model is behaving unusually well, but they should not be generalized without reviewing source mix, event mix, and stat coverage.

| Tour | Surface | Format | Event | Draw | Source coverage | N | Source share | Serve/return availability | Log loss | ROC-AUC |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| ATP | clay | best_of_3 | challenger_level | qualifying | fallback_archive | 369 | 1.000 | 0.534 | 0.3357 | 0.9303 |
| ATP | hard | best_of_3 | challenger_level | qualifying | fallback_archive | 330 | 1.000 | 0.533 | 0.4129 | 0.8914 |
| WTA | carpet | best_of_3 | itf_level | main_draw | fallback_archive | 271 | 1.000 | 0.210 | 0.4635 | 0.8717 |
| WTA | hard | best_of_3 | itf_level | main_draw | fallback_archive | 9,221 | 1.000 | 0.239 | 0.5156 | 0.8310 |
| WTA | clay | best_of_3 | itf_level | main_draw | fallback_archive | 6,894 | 1.000 | 0.207 | 0.5209 | 0.8250 |

This is the right kind of warning sign: not evidence that the model is wrong, but evidence that the strongest-looking slices are partly source-specific and should be narrated carefully.

## What This Does And Does Not Claim

This analysis supports a modest claim: transparent, pre-match tennis features beat raw rankings for baseline match outcome prediction. It does not claim causal effects, betting edge, player development prescriptions, or production-grade commercial coverage.

Known caveats:

- The data remains CC BY-NC-SA non-commercial.
- Serve/return coverage varies by source, era, tour, and event class.
- The fallback archive source requires explicit attribution and source-composition caveats.
- Missing-rank rows are not a random sample of professional tennis.
- The model is descriptive/predictive, not causal.

## Reproduce

```bash
uv run tennis-sabermetrics evaluate-match-baselines
uv run tennis-sabermetrics evaluate-match-diagnostics --fail-on-unmapped-events
uv run tennis-sabermetrics evaluate-match-walk-forward \
  --first-test-year 2016 \
  --last-test-year 2025 \
  --validation-years 3
uv run tennis-sabermetrics export-match-article-charts
```

Companion materials:

- [Notebook](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/notebooks/why_elo_serve_return_beat_rankings.ipynb)
- [Model card](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/model-cards/match-outcome-baseline.md)
- [Publication review](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/licenses/publication-review-match-baseline.md)
- [Event-level mapping notes](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/methodology/event-level-mapping.md)

## Attribution

Data derived from Jeff Sackmann / Tennis Abstract repositories and/or The Tennis Abstract Match Charting Project. Original sources are licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International unless otherwise stated. This project is non-commercial research/portfolio work and does not redistribute raw third-party data.

These baseline research metrics are not betting advice.
