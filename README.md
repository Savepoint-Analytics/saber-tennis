# Tennis Empirical Analysis

Python-first tennis sabermetrics project for Savepoint Analytics. The goal is to build a reproducible system for tennis data acquisition, warehouse modeling, match prediction, serve/return decomposition, Elo ratings, point-state simulation, and public portfolio research.

This repository stores code, docs, schemas, tests, and tiny synthetic fixtures only. Bulk third-party raw data belongs in MinIO or another configured external storage location, not Git.

## Current Phase

Phase 1 scaffold is in place:

- Source/license registry seed data.
- PostgreSQL bootstrap SQL for `tennis.source_license` and `tennis.raw_manifest`.
- Dry-run source sync CLI for canonical Tennis Abstract / Jeff Sackmann sources.
- Checksum manifest helpers.
- Initial score parser, point-string parser, temporal splits, and Elo baseline.
- Documentation for project layout, licensing, pipelines, and leakage-safe backtesting.

## Quickstart

```bash
uv sync --extra dev
uv run tennis-sabermetrics --help
uv run tennis-sabermetrics sync-sources --dry-run
uv run ruff check .
uv run pytest
```

Local configuration starts from:

```bash
cp .env.example .env
```

Never commit real secrets or raw third-party datasets.

## Repository Layout

```text
src/tennis_sabermetrics/   reusable Python package
tests/                     parser, leakage, manifest, and model tests
data/                      docs and tiny license-safe fixtures only
dbt/                       future PostgreSQL transformations
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
4. Build ATP/WTA bronze Parquet conversion.
5. Expand score parsing and no-lookahead Elo tests before training models.

## Modeling Guardrails

- Use temporal or walk-forward validation for match prediction.
- Compute all pre-match features as of match date.
- Compare against ranking, Elo, surface Elo, serve/return, and legally isolated odds baselines where available.
- Report log loss, Brier score, ROC-AUC, calibration, sample size, time period, and missingness caveats.
- Never frame outputs as gambling advice.

