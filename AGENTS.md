# AGENTS.md — Tennis Sabermetrics Project

_Last updated: 2026-06-28_

## Purpose

This file gives coding agents practical execution rules for the Tennis Empirical Analysis project.

It is derived from:
- `COMPANY_CONTEXT.md`
- `PROJECT_CONTEXT.md`
- `CLAUDE.md`
- `registry.md`
- `public-data-sources.md`

Agents must follow this file when editing code, adding data sources, creating models, writing docs, or generating public outputs.

---

## Project Identity

**Project:** Tennis Empirical Analysis  
**Vertical:** Sports Sabermetrics / Tennis Analytics  
**Owner:** Alex Oswald / Savepoint Analytics  
**Primary language:** Python  
**Secondary language:** R only when clearly useful  
**Infrastructure target:** Savepoint-Lab headless Ubuntu Server with Docker, PostgreSQL, MinIO, Prefect, and MLflow.

---

## Non-Negotiable Rules

1. **Do not commit bulk third-party raw data to Git.**
2. **Do not redistribute raw third-party data unless the license explicitly allows it.**
3. **Do not use non-commercial datasets for paid/commercial outputs.**
4. **Do not copy code from unlicensed GitHub repos.**
5. **Do not use random train/test splits for match prediction.**
6. **Do not allow future information into pre-match features.**
7. **Do not frame model outputs as gambling advice.**
8. **Always track source URL, commit/date, license, snapshot date, and checksum.**
9. **Always include attribution for Tennis Abstract / Jeff Sackmann-derived outputs.**
10. **Prefer simple tested modules over giant notebooks.**

---

## Licensing Rules for Agents

### Jeff Sackmann / Tennis Abstract Data

Treat the following as CC BY-NC-SA 4.0 unless a source-specific license says otherwise:

- `JeffSackmann/tennis_atp`
- `JeffSackmann/tennis_wta`
- `JeffSackmann/tennis_MatchChartingProject`
- `JeffSackmann/tennis_slam_pointbypoint`
- `JeffSackmann/tennis_pointbypoint`
- `JeffSackmann/tennis_misc`
- Tennis Abstract Elo pages

Agent implications:

- Public non-commercial research and portfolio artifacts are allowed with attribution.
- Paid Savepoint Analytics deliverables are not allowed from these datasets unless written permission or commercial license exists.
- Raw data should live in MinIO, not Git.
- Generated examples should use tiny fixtures created by the project or license-safe samples.
- Any derived public table must be reviewed for whether it effectively republishes restricted data.

### Forks and Unlicensed Repos

The user listed forks such as `oz-tmg/tennis_atp`, `ppaulojr/tennis_wta`, `satya469/tennis_viz`, and `halepmania/*`.

Agents must:

- Prefer canonical `JeffSackmann/*` sources.
- Treat forks as reference-only unless there is a specific reason and clear license metadata.
- Never copy unlicensed fork code.
- Never assume “public GitHub” means “free for commercial use.”

---

## Recommended Commands

Use `uv` for Python dependency management.

```bash
# Initialize project if needed
uv init
uv add pandas polars numpy duckdb pyarrow sqlalchemy psycopg pydantic pandera scikit-learn xgboost lightgbm statsmodels scipy optuna mlflow plotly dash typer rich
uv add --dev pytest ruff mypy ipykernel

# Run checks
uv run ruff check .
uv run pytest
uv run mypy src || true

# Run CLI examples once implemented
uv run tennis-sabermetrics --help
uv run tennis-sabermetrics sync-sources --dry-run
uv run tennis-sabermetrics build-bronze --source jeffsackmann_tennis_atp
uv run tennis-sabermetrics train-elo --tour atp
```

Use dbt only after staging schemas exist:

```bash
cd dbt
dbt debug
dbt run
dbt test
```

---

## Environment Variables

Use `.env` locally. Never commit real secrets.

```text
POSTGRES_HOST=savepoint-lab.local
POSTGRES_PORT=5432
POSTGRES_DB=sports
POSTGRES_SCHEMA=tennis
POSTGRES_USER=alex
POSTGRES_PASSWORD=change_me

MINIO_ENDPOINT=http://savepoint-lab.local:9000
MINIO_BUCKET=tennis-sabermetrics
MINIO_ACCESS_KEY=change_me
MINIO_SECRET_KEY=change_me

MLFLOW_TRACKING_URI=http://savepoint-lab.local:5000
PREFECT_API_URL=http://savepoint-lab.local:4200/api

RAW_DATA_ROOT=/mnt/data/tennis/raw
EXTERNAL_REPOS_ROOT=/mnt/data/tennis/external
```

---

## Repository Layout Rules

Expected layout:

```text
tennis-sabermetrics/
├── CLAUDE.md
├── AGENTS.md
├── COMPANY_CONTEXT.md
├── PROJECT_CONTEXT.md
├── registry.md
├── public-data-sources.md
├── pyproject.toml
├── data/
│   ├── README.md
│   └── fixtures/
├── docs/
├── notebooks/
├── src/tennis_sabermetrics/
├── dbt/
├── flows/
├── scripts/
├── tests/
└── outputs/
```

Rules:

- `src/tennis_sabermetrics/` contains reusable code.
- `notebooks/` are exploratory and must not be the only place important logic exists.
- `tests/fixtures/` may contain tiny synthetic or license-safe examples only.
- `data/` should contain documentation and tiny fixtures, not real third-party bulk data.
- `outputs/` should be gitignored unless output is small, public, and license-safe.

---

## Data Layer Rules

### Raw Layer

- Save exact source files to MinIO.
- Record commit SHA and checksums.
- Do not modify raw files.
- Do not load unverified-license sources into default public marts.

### Bronze Layer

- Convert source files to Parquet.
- Add metadata columns where practical:
  - `_source_key`
  - `_source_url`
  - `_source_commit_sha`
  - `_snapshot_date`
  - `_ingested_at`
  - `_license_name`

### Silver Layer

Normalize:

- Players.
- Tournaments.
- Matches.
- Rankings.
- Match stats.
- Point sequences.
- Shot charting.
- Surfaces and indoor/outdoor flags.

### Gold Layer

Build feature and analytics marts:

- Player surface strength.
- Serve/return components.
- Match features as-of date.
- Elo ratings.
- Point-state win probability.
- Prediction backtests.
- Counterfactual simulation inputs/outputs.

---

## Database Rules

Use PostgreSQL schema `tennis`.

Minimum metadata tables:

- `tennis.source_license`
- `tennis.raw_manifest`

Do not ingest source data unless a `source_license` row exists.

Recommended source keys:

```text
jeffsackmann_tennis_atp
jeffsackmann_tennis_wta
jeffsackmann_match_charting
jeffsackmann_slam_pointbypoint
jeffsackmann_pointbypoint
jeffsackmann_tennis_misc
jeffsackmann_tennis_viz
tennisabstract_atp_elo
tennisabstract_wta_elo
tennis_data_co_uk_unverified
tml_database_unverified
```

---

## Modeling Rules

### Temporal Validation

- Use train/validation/test splits by match date.
- Use walk-forward validation where possible.
- Never shuffle match rows for predictive evaluation.
- Persist split definitions and random seeds.

### Required Metrics

For match outcome probability models:

- Log loss.
- Brier score.
- ROC-AUC.
- Calibration curve.
- Accuracy only as a secondary metric.

For point/game/set simulators:

- Calibration by score state.
- Error by surface.
- Error by player strength bucket.
- Sensitivity to serve/return assumptions.

### Baselines

Always compare against:

1. Official ranking difference.
2. Overall Elo.
3. Surface Elo.
4. Serve/return component model.
5. Betting odds if legally available and isolated.

---

## Feature Engineering Rules

Every feature must answer:

- Would this be known before the match?
- Is it computed only from prior matches?
- Is it surface-specific or all-surface?
- What sample size supports it?
- Does it need shrinkage/regression to mean?
- Is it stable enough to publish?

Common feature groups:

- Elo and surface Elo.
- Recent form windows: 5/10/25/52-week windows.
- Serve stats.
- Return stats.
- Break and hold stats.
- Match format.
- Surface.
- Tournament level.
- Rest/fatigue/travel proxies.
- Head-to-head, heavily shrunk.
- Age/handedness/height where available.

---

## Testing Requirements

Add or maintain tests for:

- Score parsing.
- Point sequence parsing.
- Tiebreak handling.
- Best-of-three vs best-of-five handling.
- Player ID normalization.
- As-of-date joins.
- Elo update ordering.
- No future leakage.
- License manifest existence.
- Raw data not committed to Git.

Example test names:

```text
test_score_parser.py
test_point_parser.py
test_tiebreak_parser.py
test_elo_no_lookahead.py
test_asof_features.py
test_temporal_split.py
test_license_manifest.py
test_no_raw_data_in_git.py
```

---

## Documentation Rules

When adding a new dataset, update:

1. `registry.md`
2. `public-data-sources.md`
3. `docs/licenses/third-party-data.md` if it exists
4. `tennis.source_license` seed data
5. Any pipeline README affected

When adding a model, document:

- Objective.
- Training data period.
- Prediction target.
- Feature availability timing.
- Validation split.
- Metrics.
- Known failure modes.
- Whether it is descriptive, predictive, or causal.

---

## Public Output Rules

Every public chart/article/dashboard must include:

- Data source attribution.
- Snapshot date.
- Time period.
- Tours covered.
- Surface filters.
- Sample size.
- Missingness caveat.
- Commercial-use caveat if relevant.

Use this attribution where applicable:

> Data derived from Jeff Sackmann / Tennis Abstract repositories and/or The Tennis Abstract Match Charting Project. Original sources are licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International unless otherwise stated. This project is non-commercial research/portfolio work and does not redistribute raw third-party data.

---

## Agent Workflow

Before editing:

1. Read `PROJECT_CONTEXT.md`.
2. Read relevant section of `CLAUDE.md`.
3. Check `registry.md` for source status and license.
4. Avoid data changes if license metadata is missing.

When implementing:

1. Make small commits/patches.
2. Add tests with each parser/model change.
3. Keep notebooks thin.
4. Keep model evaluation immutable.
5. Update docs when behavior changes.

Before finishing:

1. Run `uv run ruff check .`.
2. Run `uv run pytest`.
3. Run dbt tests if dbt models changed.
4. Confirm no bulk raw data is staged.
5. Confirm attribution/license docs are updated.

---

## Things Agents Must Ask or Flag

Flag immediately if:

- A requested output appears commercial while using non-commercial data.
- A repo has no visible license.
- A feature might leak future information.
- A model shows suspiciously high performance.
- A public output may effectively republish raw restricted data.
- A source requires scraping and terms are unclear.

Do not block progress unnecessarily. If a license is unclear, isolate the source and continue with canonical verified sources.

---

## Suggested First Tasks

1. Create `src/tennis_sabermetrics/config.py` with paths and source keys.
2. Create seed data for `tennis.source_license`.
3. Implement `sync_sources.py --dry-run` for canonical GitHub repos.
4. Implement checksum manifest generation.
5. Build ATP/WTA bronze Parquet conversion.
6. Write score parser tests.
7. Implement baseline Elo with no-lookahead tests.

---

## Update Log

| Date | Update |
|---|---|
| 2026-06-28 | Initial AGENTS.md derived from project, company, Claude, registry, and public source context. |
