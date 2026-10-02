# Tennis Empirical Analysis

Python-first tennis sabermetrics project for Savepoint Analytics. The goal is to build a reproducible system for tennis data acquisition, warehouse modeling, match prediction, serve/return decomposition, Elo ratings, point-state simulation, and public portfolio research.

This repository stores code, docs, schemas, tests, and tiny synthetic fixtures only. Bulk third-party raw data belongs in MinIO or another configured external storage location, not Git.

## Current Phase

Phase 1 scaffold is in place:

- Source/license registry seed data.
- PostgreSQL bootstrap SQL for `tennis.source_license` and `tennis.raw_manifest`.
- Dry-run and local clone/fetch source sync CLI for canonical Tennis Abstract / Jeff Sackmann sources.
- Optional MinIO raw snapshot copy and PostgreSQL raw manifest persistence from source sync.
- Checksum manifest helpers that skip repository internals.
- ATP/WTA bronze CSV-to-Parquet batch conversion with required metadata columns.
- Score parser, point-string parser, temporal splits, overall Elo, independent surface Elo, and blended surface Elo with sparse-surface shrinkage.
- Documentation for project layout, licensing, pipelines, and leakage-safe backtesting.
- Source availability decision record for current ATP/WTA canonical GitHub blockage and a reviewed archival fallback.
- Explicit fallback archive subdirectory sync for ATP/WTA, raw MinIO manifest writes, and fallback bronze Parquet outputs.
- Initial dbt staging models for source licenses, raw manifests, players, tournaments, matches, rankings, and match stats.
- PostgreSQL bronze landing-table loader, raw-manifest row-count enrichment, and verified dbt Postgres run/test workflow.
- Player-file bronze conversion for ATP/WTA players, stricter bronze schema validation helpers, and silver dbt models for normalized players, tournaments, matches, rankings, and match stats.
- PostgreSQL `gold_match_features_asof` feature table for post-1990 ATP/WTA matches, with hash-oriented players, rankings, Elo, blended surface Elo, rest/form, and serve/return features frozen before match date.
- Baseline match-outcome evaluation for ranking difference, overall Elo, blended surface Elo, a logistic baseline, and validation-fitted Platt/isotonic calibrated variants.
- Python and dbt leakage gates that validate feature timing, match-feature grain, self-match exclusions, and joined difference features before model evaluation.
- Calibration, missingness, segmented backtest, and source-composition diagnostics for baseline match prediction, including event-level, qualifying/main-draw, ranking-population, and source-coverage flags.
- 2016-2025 walk-forward evaluation windows for ranking, Elo, surface Elo, logistic, Platt, and isotonic variants.
- Draft public non-commercial article, notebook, model card, and publication review for “Why Elo and serve/return decomposition beat raw rankings.”
- Source-aware event-level mapping and a current commercial data path for future paid tennis analytics.

## Quickstart

```bash
uv sync --extra dev
uv run tennis-sabermetrics --help
uv run tennis-sabermetrics sync-sources --dry-run
uv run tennis-sabermetrics build-bronze --source jeffsackmann_tennis_atp --snapshot-date 2026-07-15
uv run tennis-sabermetrics build-bronze --source aneeshers_tennis_sackmann_archive --archive-tour atp --snapshot-date 2026-08-25 --source-root .local/external/tennis-sackmann-archive --bronze-root .local/bronze
uv run tennis-sabermetrics load-bronze-postgres --bronze-root .local/bronze --snapshot-date 2026-08-25
uv run tennis-sabermetrics enrich-raw-manifest-row-counts --source-root .local/external/tennis-sackmann-archive --snapshot-date 2026-08-25
uv run tennis-sabermetrics build-gold-match-features --snapshot-date 2026-08-25 --start-date 1990-01-01
uv run tennis-sabermetrics evaluate-match-baselines
uv run tennis-sabermetrics evaluate-match-diagnostics
uv run tennis-sabermetrics evaluate-match-walk-forward
uv run tennis-sabermetrics export-match-article-charts
uv run ruff check .
uv run pytest
```

Local configuration starts from:

```bash
cp .env.example .env
```

The CLI loads `.env` automatically. It accepts the canonical `POSTGRES_*` and `MINIO_*` names plus Savepoint aliases such as `SAVEPOINT_PG_*` and `SAVEPOINT_MINIO_*`. If `MINIO_ENDPOINT` points at the console port and `MINIO_PORT` is set, the CLI normalizes writes to the S3 API port.

Never commit real secrets or raw third-party datasets.

## Repository Layout

```text
src/tennis_sabermetrics/   reusable Python package
tests/                     parser, leakage, manifest, and model tests
data/                      docs and tiny license-safe fixtures only
dbt/                       PostgreSQL staging and silver transformations
flows/                     future Prefect orchestration entry points
scripts/                   bootstrap and operational scripts
docs/                      methodology, data dictionaries, licenses, pipelines
outputs/                   local generated outputs, ignored by Git
```

See [docs/project-layout.md](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/project-layout.md) for more detail.

## Data And Licensing

The core public tennis sources are treated as CC BY-NC-SA 4.0 unless source-specific license metadata says otherwise. They are suitable for non-commercial public research/portfolio work with attribution, but not paid Savepoint Analytics deliverables without permission or another commercial data source.

Required attribution for public outputs that use Tennis Abstract / Jeff Sackmann-derived data:

> Data derived from Jeff Sackmann / Tennis Abstract repositories and/or The Tennis Abstract Match Charting Project. Original sources are licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International unless otherwise stated. This project is non-commercial research/portfolio work and does not redistribute raw third-party data.

See [docs/licenses/third-party-data.md](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/licenses/third-party-data.md) and [docs/licenses/attribution.md](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/licenses/attribution.md).

## First Milestones

1. Bootstrap PostgreSQL metadata tables with `scripts/bootstrap_postgres.sql`.
2. Run `tennis-sabermetrics sync-sources --dry-run` and confirm source metadata.
3. Sync canonical ATP/WTA repositories into external storage, recording commit SHA and checksums.
4. Run source sync with `--copy-raw-to-minio --write-raw-manifest` once MinIO/PostgreSQL credentials are configured.
5. Build first dbt staging models over source license, raw manifest, players, matches, rankings, and match stats.
6. Expand score parsing and no-lookahead Elo tests before training models.

Current acquisition note: as of 2026-08-25, MinIO and PostgreSQL connectivity are verified. Canonical ATP/WTA GitHub endpoints returned 404 from local Git/curl checks, so fallback ATP/WTA raw snapshots were synced from `Aneeshers/tennis-sackmann-archive` under the same CC BY-NC-SA restrictions. Local working clones and bronze outputs are under ignored `.local/` paths, not `data/`. PostgreSQL bronze landing tables, dbt staging views, and dbt silver views are built. Canonical source keys were not silently remapped. See [docs/pipelines/source-availability.md](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/pipelines/source-availability.md).

## Current Analytics Status

The warehouse can support descriptive ATP/WTA match analytics now. The current silver layer contains normalized views for players, tournaments, matches, rankings, and match stats. The current gold feature table contains 1,538,042 post-1990 matches, has zero `max_feature_asof_date >= match_date` violations, zero self-match rows, and a hash-oriented `player_a_won` rate of 0.499856. Python leakage checks run before model evaluation.

Match prediction is now possible for baseline non-commercial research. Current test-period metrics for 2022 onward:

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

These are baseline research metrics, not betting advice. Public outputs need attribution, snapshot date, time period, sample size, missingness/source-composition caveats, and non-commercial caveats.

Current diagnostics:

- `tennis.gold_prediction_calibration`: 160 rows and `outputs/charts/match_prediction_calibration.html`.
- `tennis.gold_feature_missingness`: 648 rows.
- `tennis.gold_segment_backtests`: 1,164 rows.
- `tennis.gold_source_composition_diagnostics`: 159 rows.
- `tennis.gold_event_level_mapping_diagnostics`: 38 rows, with 0 unmapped source rows.
- `tennis.gold_prediction_walk_forward_backtests`: 120 rows.
- Largest logistic test calibration errors are now roughly 1-2 percentage points after hash orientation removed the prior side-assignment bias.
- Isotonic has the smallest worst-bin logistic calibration error, while the uncalibrated logistic baseline keeps the best held-out log loss.
- High-performing missing-rank test segments are currently 100% from `aneeshers_tennis_sackmann_archive` and concentrated in specific event/draw populations, so those segment results require source-composition review before publication.

Walk-forward 2016-2025 average test metrics across 550,657 annual test rows:

| Model | Avg log loss | Avg Brier | Avg ROC-AUC | Avg accuracy |
|---|---:|---:|---:|---:|
| Logistic baseline | 0.586946 | 0.201187 | 0.754366 | 0.685356 |
| Logistic baseline Platt | 0.586974 | 0.201198 | 0.754366 | 0.685470 |
| Logistic baseline isotonic | 0.587070 | 0.201232 | 0.754248 | 0.685216 |
| Overall Elo | 0.594394 | 0.204121 | 0.746775 | 0.680254 |
| Blended surface Elo | 0.601479 | 0.207252 | 0.738765 | 0.674004 |
| Ranking log difference | 0.646298 | 0.227138 | 0.671815 | 0.616726 |

Publication-ready non-commercial artifacts:

- [docs/articles/why-elo-serve-return-beat-rankings.md](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/articles/why-elo-serve-return-beat-rankings.md)
- [notebooks/why_elo_serve_return_beat_rankings.ipynb](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/notebooks/why_elo_serve_return_beat_rankings.ipynb)
- [docs/model-cards/match-outcome-baseline.md](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/model-cards/match-outcome-baseline.md)
- [docs/licenses/publication-review-match-baseline.md](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/licenses/publication-review-match-baseline.md)
- [docs/methodology/event-level-mapping.md](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/methodology/event-level-mapping.md)
- [docs/pipelines/commercial-data-path.md](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/pipelines/commercial-data-path.md)

Static article chart exports are generated under ignored `outputs/charts/article/`.

Baseline, diagnostics, and walk-forward model refreshes use snapshot-aware feature caches under ignored `outputs/cache/` by default. Use `--no-feature-cache` when you need to force a fresh PostgreSQL read.

## Modeling Guardrails

- Use temporal or walk-forward validation for match prediction.
- Compute all pre-match features as of match date.
- Compare against ranking, Elo, surface Elo, serve/return, and legally isolated odds baselines where available.
- Report log loss, Brier score, ROC-AUC, calibration, sample size, time period, and missingness caveats.
- Never frame outputs as gambling advice.
