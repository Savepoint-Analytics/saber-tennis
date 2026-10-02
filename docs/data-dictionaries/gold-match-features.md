# Gold Match Features As-Of

`tennis.gold_match_features_asof` is the first prediction-ready feature table.

Build command:

```bash
uv run tennis-sabermetrics build-gold-match-features \
  --snapshot-date 2026-08-25 \
  --start-date 1990-01-01
```

Current build:

- Rows: 1,538,042
- Match date range: 1990-01-01 to 2026-06-02
- Future-feature violations: 0
- Self-match rows: 0
- Rows with tournament level populated: 1,538,042
- Rows with draw size populated: 1,538,042
- Rows with both player rankings available: 1,280,284
- `player_a_won` rate: 0.499856

## Grain

One row per singles match after duplicate raw match records are collapsed by source, tour, match ID, tournament, match date, winner, and loser.

Players are oriented deterministically:

- `player_a_id` is assigned by a stable SHA-256 hash of source, tour, match ID, tournament, and match date.
- `player_b_id` is the other player in the match.
- `player_a_won` is the binary prediction target.

This avoids the invalid modeling pattern where the row is always oriented as winner versus loser, while also avoiding side assignment based on player ID ordering.

## Feature Timing

All features are computed from information known before the match date:

- Rankings use the latest ranking date strictly before `match_date`.
- Overall Elo and blended surface Elo are snapshotted before matches on that date.
- Prior win rate, recent 10-match form, rest days, and serve/return rates are updated only after all matches for a date have been feature-snapshotted.
- `max_feature_asof_date` must be null or earlier than `match_date`.
- `player_a_id` and `player_b_id` must be distinct.

This conservative date-level freeze avoids same-day leakage when exact match start times are unavailable.

## Feature Groups

| Group | Columns |
|---|---|
| Match identity | `source_key`, `tour`, `match_id`, `tournament_id`, `match_date`, `surface`, `round`, `best_of`, `tournament_level`, `draw_size` |
| Target orientation | `player_a_id`, `player_b_id`, `player_a_won` |
| Rankings | `player_a_rank`, `player_b_rank`, `player_a_ranking_points`, `player_b_ranking_points`, `rank_diff`, `rank_log_diff` |
| Elo | `player_a_overall_elo`, `player_b_overall_elo`, `overall_elo_diff`, `player_a_surface_elo`, `player_b_surface_elo`, `surface_elo_diff` |
| Form/rest | `player_a_prior_matches`, `player_b_prior_matches`, prior win rates, recent 10 win rates, rest days |
| Serve/return | Prior serve-points-won percentage, prior return-points-won percentage, and player A minus player B differences |
| Guardrails | `max_feature_asof_date`, `snapshot_date` |

## Caveats

- The current build uses the fallback archive source key `aneeshers_tennis_sackmann_archive` and remains bound by CC BY-NC-SA non-commercial restrictions.
- Serve/return features are null until a player has prior matches with source stat coverage.
- Doubles files are not part of the current singles feature contract.
- `tournament_level` and `draw_size` are source-derived event metadata. Diagnostics map `tournament_level` into coarse event classes and `round` into qualifying/main-draw flags; these labels should still be reviewed by source before publication claims.
- The `player_*_surface_elo` columns are blended surface ratings: sparse surface histories are shrunk toward each player's overall Elo before match prediction.
- The table is suitable for baseline research. Model evaluation runs Python leakage checks first, and dbt has singular tests for no future dates, unique feature grain, player distinctness, and difference-column consistency.
- Calibration, missingness, and segmented backtest diagnostics are available through `tennis-sabermetrics evaluate-match-diagnostics`.
- Production-grade claims still need source-composition review, especially for high-performing missing-rank segments.
