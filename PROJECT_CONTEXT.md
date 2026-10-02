# PROJECT_CONTEXT.md — Sports Sabermetrics — Tennis Empirical Analysis

_Last updated: 2026-09-28_

## Purpose

This document preserves the longitudinal context for the Sports Sabermetrics / Tennis Empirical Analysis project.

Use it so future AI sessions, development sessions, and planning sessions do not restart from zero.

This document captures:
- Decisions made and why.
- Work already completed.
- Open questions.
- Current priorities.
- Tasks in progress.
- Things tried that did not work.
- Changes in direction.
- Important context that must survive across sessions.

Standing instructions belong in `CLAUDE.md`.
Business source-of-truth belongs in `COMPANY_CONTEXT.md`.
Project history and working context belong here.
Coding-agent execution rules belong in `AGENTS.md`.
Dataset inventory and acquisition status belong in `registry.md`.
Source-specific acquisition, access, and licensing notes belong in `public-data-sources.md`.

---

## Project Summary

**Vertical:** Sports Sabermetrics / Tennis Analytics  
**Project name:** Tennis Empirical Analysis  
**Primary goal:** Build a reproducible, Python-centric tennis analytics system that explains and predicts match outcomes from point, game, set, match, player, surface, and tactical data.  
**Portfolio purpose:** Demonstrate rigorous sports analytics outside of video games; build domain credibility for Savepoint Analytics; create affordable public-facing tennis analysis while respecting non-commercial data licenses.  
**Public or private:** Public GitHub portfolio for code, docs, methodology, and derived non-sensitive analysis; raw third-party datasets must not be redistributed unless their licenses explicitly allow it.  
**Founder/operator:** Alex Oswald / Savepoint Analytics.  
**Infrastructure target:** Savepoint-Lab headless Ubuntu Server with Docker, PostgreSQL, MinIO, Prefect, and MLflow.

---

## Current Phase

- [x] Phase 0: Context, source inventory, and licensing constraints defined.
- [ ] Phase 1: Data acquisition and raw snapshot pipeline. Initial scaffold and metadata guardrails created.
- [ ] Phase 2: Core tennis warehouse model and validation checks.
- [ ] Phase 3: First publishable artifact: Elo + serve/return decomposition by surface.
- [ ] Phase 4: Point/game/set win-probability simulator.
- [ ] Phase 5: Public dashboard or article series.

**Current focus:** Prepare the first non-commercial match-prediction artifact for careful publication by adding lightweight chart captions, source-specific review notes, and runtime improvements.

---

## Domain Context

### What This Project Is About

Tennis sabermetrics studies how points, games, sets, matches, surfaces, players, tactics, serve patterns, return patterns, fatigue, and pressure situations contribute to winning. The project should support both descriptive analysis and predictive modeling: who is likely to win, why they are likely to win, which phase of play matters most, and how counterfactual tactical changes could affect outcomes.

The audience includes tennis players, coaches, analysts, technical hiring managers, sports analytics readers, and future Savepoint Analytics clients. The analytical standard should be higher than casual tennis commentary: every claim should connect back to a model, metric, uncertainty interval, or reproducible data slice.

### Key Terminology

| Term | Definition |
|---|---|
| Hold percentage | Percentage of service games won by a player. One of the core tennis strength measures. |
| Break percentage | Percentage of return games won by a player. |
| Service points won | Share of points won while serving. More stable than match win rate over smaller samples. |
| Return points won | Share of points won while returning. Critical for separating return skill from serve dominance. |
| First-serve percentage | Share of service points where the first serve lands in. |
| First-serve points won | Share of points won after a made first serve. |
| Second-serve points won | Share of points won after a second serve. Strong diagnostic of vulnerability under pressure. |
| Ace rate | Aces divided by service points, not by service games. |
| Double-fault rate | Double faults divided by service points. |
| Dominance ratio | Return points won divided by opponent return points won, often used by Tennis Abstract. |
| Elo rating | Dynamic strength rating updated after matches. More predictive than raw rankings because opponent strength matters. |
| Surface Elo | Elo variant computed or blended by surface: hard, clay, grass, indoor/hard where available. |
| Best-of-three / best-of-five | Match formats with different volatility and underdog upset probabilities. |
| Tiebreak | Special game used to decide a set at 6-6 in many formats. Needs separate modeling due to serve alternation. |
| Pressure point | Informal term for points with high leverage, such as break points, set points, match points, or late tiebreak points. |
| Win probability | Estimated probability that a player wins a game, set, or match from a given state. |
| Counterfactual simulation | Simulating how outcomes change if a player improves or changes a component, such as second-serve win rate or return depth. |
| Shot charting | Structured point-level coding of shot type, direction, depth, errors, winners, net approaches, and rally patterns. |

### Key Questions This Project Answers

1. Which player is likely to win a given match, and how does that probability change by surface and format?
2. Which components explain the forecast: serve strength, return strength, surface adaptation, recent form, fatigue, head-to-head, or matchup style?
3. How do points convert into games, games into sets, and sets into match outcomes?
4. Which specific tactical improvements would most improve a player’s win probability?
5. How much of a player’s performance is surface-specific versus generally portable across surfaces?
6. Which players are over- or under-rated by official rankings compared with Elo, serve/return metrics, and point-level data?
7. Which in-match states are most sensitive to coaching-relevant interventions?
8. Can transparent models rival black-box models for prediction while providing more useful coaching explanations?

---

## Data Sources

### Primary Datasets

| Dataset | Source | Format | Update Frequency | Status | Notes |
|---|---|---|---|---|---|
| Tennis Abstract ATP match/ranking data | `https://github.com/JeffSackmann/tennis_atp` | CSV | Regular but not guaranteed | Target | Canonical ATP source. Match stats mostly 1991+, stronger from 1997+. CC BY-NC-SA 4.0. |
| Tennis Abstract WTA match/ranking data | `https://github.com/JeffSackmann/tennis_wta` | CSV | Regular but not guaranteed | Target | Canonical WTA source. CC BY-NC-SA 4.0. |
| Aneeshers Tennis Sackmann Archive | `https://github.com/Aneeshers/tennis-sackmann-archive` | CSV | Archival mirror | Fallback | Reviewed mirror for ATP/WTA/Slam point-by-point availability gaps. Keep separate source key, original Jeff Sackmann attribution, mirror provenance, CC BY-NC-SA 4.0 constraints, and non-commercial handling. |
| Tennis Abstract Match Charting Project | `https://github.com/JeffSackmann/tennis_MatchChartingProject` | CSV | Periodic | Target | Shot-by-shot and point-level charted matches. Best public source for tactics. CC BY-NC-SA 4.0. |
| Grand Slam point-by-point | Prefer canonical `https://github.com/JeffSackmann/tennis_slam_pointbypoint`; user also listed `github.com/halepmania/tennis_slam_pointbypoint` | CSV | After slams, not guaranteed | Target | Slam point data; availability and columns vary by year/tournament. CC BY-NC-SA 4.0 in canonical repo. |
| Sequential point-by-point | Prefer canonical `https://github.com/JeffSackmann/tennis_pointbypoint`; user listed `https://github.com/ppaulojr/tennis_pointbypoint` | CSV | Historical/static-ish | Target | Encoded point sequences for thousands of matches. Data is messy and incomplete. CC BY-NC-SA 4.0 in canonical repo. |
| Tennis Abstract Elo ratings | `https://tennisabstract.com/reports/atp_elo_ratings.html`, `https://tennisabstract.com/reports/wta_elo_ratings.html` | HTML tables | Weekly-ish | Target | Use as benchmark and reference, not as a black box to copy blindly. |
| Tennis Abstract visualization examples | Prefer canonical `https://github.com/JeffSackmann/tennis_viz`; user listed `https://github.com/satya469/tennis_viz` | Python/Altair/data snippets | Static examples | Reference only | Useful for analysis ideas; license unclear for forked code, so do not copy code unless license verified. |
| Tennis misc algorithms | Prefer canonical `https://github.com/JeffSackmann/tennis_misc`; user listed `https://github.com/halepmania/tennis_misc` | Python scripts | Static | Reference only | Probability algorithms. CC BY-NC-SA 4.0 in canonical repo; do not commercialize without permission. |
| Tennis-Data.co.uk | `https://www.tennis-data.co.uk/` | CSV/XLS | Current + historical | Optional/private experiment | Includes betting odds and results. License/terms need verification before any redistribution or commercial use. |
| Ultimate Tennis Statistics / Tennis Crystal Ball | `https://github.com/mcekovic/tennis-crystal-ball` | Java app, algorithms | Active-ish | Reference only | Code Apache-2.0; algorithms CC BY-NC-SA 4.0. Useful for feature ideas and Elo variants. |
| tennis-xgboost-autoresearch | `https://github.com/buildoak/tennis-xgboost-autoresearch` | Python | Current | Reference only | Useful for evaluation design and Goodhart-proofing. Code MIT; bundled data CC BY-NC-SA 4.0. |
| jgollub1 tennis_match_prediction | `https://github.com/jgollub1/tennis_match_prediction` | Python/notebooks | Static | Reference only | Pre-match and in-match prediction methodology; MIT code; uses Sackmann data. |
| mxa256 tennis_preds | `https://github.com/mxa256/tennis_preds` | R | Current-ish | Reference only | Strong example of leakage-aware modeling and CLAUDE-style repo docs; R-centric. |
| serve-and-volley ATP scrape scripts | `https://github.com/serve-and-volley/atp-world-tour-tennis-data` | Python/R/SQL/CSV | Static as of 2023 | Reference only | Scrape scripts under CC BY 4.0; site redesign can break them. Verify terms before using. |
| Stats Perform WTA official feed | `https://www.statsperform.com/wta/` | Licensed API/feed | Commercial licensed | Not public | Potential commercial pathway for official WTA data, not a public dataset. |

### Data Pipeline

Recommended flow:

1. **Raw acquisition**
   - Clone or download public repositories into Savepoint-Lab.
   - Preserve raw snapshots in MinIO as immutable Parquet/CSV plus source metadata.
   - Do not commit raw third-party data to Git unless the license explicitly permits redistribution.

2. **Bronze layer**
   - Store raw source files in MinIO bucket `tennis-sabermetrics` under `raw/<source>/<snapshot_date>/`.
   - Convert CSV to Parquet for reliable downstream reads.
   - Add `_source`, `_snapshot_date`, `_ingested_at`, `_source_url`, and `_license` columns where practical.

3. **Silver layer**
   - Load normalized entities into PostgreSQL schema `tennis`:
     - `tennis.players`
     - `tennis.tournaments`
     - `tennis.matches`
     - `tennis.rankings`
     - `tennis.match_stats`
     - `tennis.points`
     - `tennis.shots`
     - `tennis.elo_ratings`
   - Use `dbt` staging models to standardize names, IDs, surfaces, rounds, dates, match formats, and score strings.

4. **Gold layer**
   - Build analytics marts in PostgreSQL and Parquet:
     - `mart_player_surface_strength`
     - `mart_match_features_asof`
     - `mart_serve_return_components`
     - `mart_point_state_win_probability`
     - `mart_counterfactual_inputs`
     - `mart_prediction_backtests`

5. **Model layer**
   - Use Python packages in `src/tennis_sabermetrics/` for feature generation, Elo updates, model training, evaluation, and simulation.
   - Track experiments in MLflow on Savepoint-Lab.
   - Save model artifacts outside Git; register metadata and metrics only.

6. **Outputs**
   - Dash/Plotly for interactive dashboards.
   - Static markdown + charts for public write-ups.
   - Optional RMarkdown or Quarto for one-off statistical reports.

### Data Acquisition Notes

- Prefer canonical Jeff Sackmann repositories over forks unless a fork contains data unavailable upstream and its license/lineage is clear.
- As of 2026-08-24, `JeffSackmann/tennis_atp` and `JeffSackmann/tennis_wta` returned repository-not-found responses from local Git/curl checks. `Aneeshers/tennis-sackmann-archive` is reviewed as a fallback, not as a silent replacement for canonical source keys.
- Do not use non-commercial third-party datasets in paid Savepoint Analytics client work without written permission or a separate commercial license.
- Keep data snapshots reproducible. Never rely only on “latest from GitHub” without recording commit hash and download date.
- Point-level and shot-level datasets contain missingness that is not random. Availability depends on tournament, court, year, scoring system, and charting coverage.
- Score parsing must handle retirements, walkovers, tiebreaks, super-tiebreaks, best-of-five formats, Davis Cup/team events, and old scoring conventions.
- Betting-odds data is useful for forecast benchmarking but may have unclear reuse rights and should be isolated from public deliverables until terms are verified.

---

## Tech Stack for This Vertical

- **Primary language:** Python.
- **Secondary language:** R for specialized statistical experiments, validation, and comparison with prior R tennis work.
- **Package/dependency manager:** `uv` for Python; `renv` only for any R subprojects.
- **Core Python libraries:** `pandas`, `polars`, `numpy`, `duckdb`, `pyarrow`, `sqlalchemy`, `psycopg`, `pydantic`, `pandera`, `scikit-learn`, `xgboost`, `lightgbm`, `statsmodels`, `scipy`, `optuna`, `mlflow`, `plotly`, `dash`, `typer`, `rich`.
- **Bayesian/uncertainty options:** `pymc` or `stan` only when the problem justifies it.
- **Warehouse / storage:** PostgreSQL on Savepoint-Lab for normalized relational data; MinIO for raw and processed files; DuckDB for local analytical iteration.
- **Orchestration:** Prefect on Savepoint-Lab.
- **Transformations:** dbt-postgres for core relational marts; Python for source-specific parsing and feature engineering.
- **Visualization:** Plotly/Dash first; static Matplotlib/Altair acceptable for articles; R Shiny only where it materially improves delivery.
- **Notebook environment:** VS Code + Jupyter notebooks, with notebooks treated as exploratory artifacts, not production pipelines.
- **Testing:** `pytest`, `ruff`, `mypy` where practical, `pandera` validation, and dbt tests.
- **Data quality:** Great Expectations or lightweight `pandera`/dbt tests; prefer simple checks early.

---

## Storage Recommendation

Use a **hybrid Savepoint-Lab architecture**:

- **MinIO is the source-of-truth for immutable raw snapshots** because these datasets arrive as CSV, HTML tables, or scraped files and should be preserved exactly as acquired.
- **PostgreSQL is the source-of-truth for normalized analytical tables** because tennis entities are relational: players, matches, rankings, tournaments, points, shots, and model features.
- **DuckDB is the local exploration engine** for fast Parquet analysis and feature prototyping without constantly loading everything into PostgreSQL.
- **Git stores code, docs, schemas, dbt models, metadata manifests, and tiny fixtures only**. Git should not store bulk third-party raw data.

Recommended location pattern:

```text
MinIO bucket: tennis-sabermetrics
  raw/jeffsackmann_tennis_atp/snapshot_date=YYYY-MM-DD/commit=<sha>/...
  raw/jeffsackmann_tennis_wta/snapshot_date=YYYY-MM-DD/commit=<sha>/...
  raw/match_charting_project/snapshot_date=YYYY-MM-DD/commit=<sha>/...
  bronze/<source>/<table>/snapshot_date=YYYY-MM-DD/*.parquet
  silver/<entity>/<snapshot_date>/*.parquet
  gold/<mart>/<snapshot_date>/*.parquet

PostgreSQL database: sports or savepoint_analytics
PostgreSQL schema: tennis
  raw_manifest
  source_license
  players
  tournaments
  matches
  rankings
  match_stats
  points
  shots
  elo_ratings
  model_predictions
  simulation_outputs
```

---

## Repository Structure

```text
tennis-sabermetrics/
├── README.md
├── CLAUDE.md
├── AGENTS.md
├── COMPANY_CONTEXT.md
├── PROJECT_CONTEXT.md
├── registry.md
├── public-data-sources.md
├── pyproject.toml
├── uv.lock
├── .python-version
├── .env.example
├── .gitignore
├── data/
│   ├── README.md
│   ├── fixtures/                  # tiny test fixtures allowed in Git
│   └── sample/                    # tiny public samples only when license permits
├── docs/
│   ├── methodology/
│   │   ├── elo.md
│   │   ├── serve-return-models.md
│   │   ├── win-probability.md
│   │   ├── counterfactuals.md
│   │   └── leakage-and-backtesting.md
│   ├── data-dictionaries/
│   ├── licenses/
│   │   ├── third-party-data.md
│   │   └── attribution.md
│   └── project-layout.md
├── notebooks/
│   ├── 00_source_audit.ipynb
│   ├── 01_atp_wta_eda.ipynb
│   ├── 02_elo_baseline.ipynb
│   ├── 03_serve_return_components.ipynb
│   └── 04_point_state_simulation.ipynb
├── src/
│   └── tennis_sabermetrics/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── ingest/
│       │   ├── git_sources.py
│       │   ├── tennis_atp.py
│       │   ├── tennis_wta.py
│       │   ├── match_charting.py
│       │   ├── slam_pointbypoint.py
│       │   └── manifests.py
│       ├── transform/
│       │   ├── normalize_players.py
│       │   ├── normalize_matches.py
│       │   ├── parse_scores.py
│       │   ├── parse_points.py
│       │   └── surfaces.py
│       ├── features/
│       │   ├── asof.py
│       │   ├── form_windows.py
│       │   ├── serve_return.py
│       │   ├── h2h.py
│       │   └── pressure.py
│       ├── models/
│       │   ├── elo.py
│       │   ├── match_outcome.py
│       │   ├── point_win_probability.py
│       │   └── calibration.py
│       ├── simulation/
│       │   ├── game.py
│       │   ├── set.py
│       │   ├── match.py
│       │   └── counterfactuals.py
│       ├── evaluation/
│       │   ├── temporal_split.py
│       │   ├── metrics.py
│       │   ├── baselines.py
│       │   └── leakage_checks.py
│       └── viz/
│           ├── charts.py
│           └── dashboards.py
├── dbt/
│   ├── dbt_project.yml
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   └── tests/
├── flows/
│   ├── ingest_sources.py
│   ├── build_warehouse.py
│   ├── train_models.py
│   └── publish_artifacts.py
├── scripts/
│   ├── bootstrap_minio.py
│   ├── bootstrap_postgres.sql
│   └── sync_sources.sh
├── tests/
│   ├── fixtures/
│   ├── test_score_parser.py
│   ├── test_point_parser.py
│   ├── test_elo_no_lookahead.py
│   ├── test_temporal_split.py
│   └── test_license_manifest.py
└── outputs/
    ├── charts/
    ├── tables/
    └── reports/
```

---

## Important Decisions Made

| Date | Area | Decision | Rationale | Revisit If |
|---|---|---|---|---|
| 2026-06-28 | Storage | Use MinIO for raw/bronze snapshots and PostgreSQL schema `tennis` for normalized/modeled data. | Preserves raw files while enabling relational modeling and dbt. | Data volume exceeds single-server comfort or a cloud deployment becomes necessary. |
| 2026-06-28 | Licensing | Treat Jeff Sackmann/Tennis Abstract datasets and algorithms as CC BY-NC-SA 4.0. | Canonical READMEs require attribution, non-commercial use, and share-alike. | Written commercial permission or alternate licensed data source is obtained. |
| 2026-06-28 | Sources | Prefer canonical JeffSackmann repos over forks listed by user. | Forks may be stale, unlicensed, or detached from canonical maintenance. | A fork contains unique, verified, license-compatible data. |
| 2026-06-28 | Modeling | Start with transparent baselines: Elo, surface Elo, serve/return decomposition, logistic models. | Coaches and analysts need explanations, not only black-box predictions. | Transparent models plateau and added complexity improves out-of-sample performance. |
| 2026-06-28 | Evaluation | Use strict temporal splits and immutable evaluation code. | Tennis data is vulnerable to leakage through rankings, future form, tournament outcomes, and rolling features. | A benchmark suite is fully established and versioned. |
| 2026-06-28 | Commercialization | Public portfolio can use non-commercial datasets; paid products require licensed data, permission, or original data collection. | Savepoint Analytics must not violate non-commercial licenses. | Commercial rights are obtained. |

---

## Work Completed

| Date | Milestone | Notes |
|---|---|---|
| 2026-06-28 | Context files created | Created project-specific `PROJECT_CONTEXT.md`, `COMPANY_CONTEXT.md`, `CLAUDE.md`, `registry.md`, `public-data-sources.md`, and `AGENTS.md`. |
| 2026-06-28 | Source list initialized | Incorporated user-specified GitHub repos and added canonical alternatives/references. |
| 2026-06-28 | Licensing model defined | Added non-commercial data guardrails and commercial-use pathway. |
| 2026-06-28 | Storage recommendation defined | Recommended Savepoint-Lab MinIO + PostgreSQL + DuckDB + Prefect + dbt. |
| 2026-06-29 | Initial repo scaffold created | Added Python package layout, README, docs, source-license seeds, PostgreSQL bootstrap SQL, dry-run source sync CLI, checksum helpers, score/point parsers, temporal split, no-lookahead Elo baseline, and initial tests. |
| 2026-07-08 | Phase 1 build-out continued | Synced local Python tooling with `uv`, added clone/fetch source-sync primitives, checksum skipping for `.git`, bronze CSV-to-Parquet metadata helper, expanded score parsing, independent surface Elo, and 20 passing tests. |
| 2026-07-15 | Raw and bronze pipeline guardrails added | Added explicit MinIO raw snapshot copy, PostgreSQL raw manifest writer, ATP/WTA `build-bronze` CLI, raw-manifest documentation, and tests for storage/manifest/bronze behavior. |
| 2026-08-04 | PostgreSQL bootstrap executed | Added `.env` autoloading and Savepoint env aliases, ran `bootstrap-postgres`, verified 11 `source_license` rows and `tennis.raw_manifest`. MinIO sync is blocked until access key and secret key are visible to the CLI. |
| 2026-08-23 | MinIO/PostgreSQL verified; canonical ATP/WTA GitHub unavailable | `.env` now exposes MinIO write credentials. MinIO bucket read and PostgreSQL metadata connectivity were verified. ATP/WTA sync was attempted but `github.com/JeffSackmann/tennis_atp` and `github.com/JeffSackmann/tennis_wta` returned 404 via Git/curl. Do not switch to forks without license review. |
| 2026-08-24 | ATP/WTA fallback reviewed | Confirmed canonical ATP/WTA repositories remain unavailable from local Git/curl checks, verified Match Charting remains accessible, reviewed `Aneeshers/tennis-sackmann-archive` as a CC BY-NC-SA fallback, and added fallback metadata/docs without remapping canonical source keys. |
| 2026-08-25 | Fallback ATP/WTA raw and bronze pipeline completed | Added explicit archive subdirectory sync, synced `atp/` and `wta/` raw snapshots from archive commit `83733587353df8a41f2fd4f516147d5aa83f5a8d` to MinIO, wrote 302 `raw_manifest` rows, built 299 local bronze Parquet files, and added initial dbt staging models. |
| 2026-08-25 | Bronze warehouse and dbt staging verified | Loaded bronze Parquet to PostgreSQL landing tables, enriched 299 raw manifest row counts, added `dbt-postgres` and repo-local profile, ran `dbt debug`, built 7 staging views, and passed 7 dbt data tests. |
| 2026-08-25 | Player-file bronze and silver warehouse completed | Added player-file bronze conversion for ATP/WTA players, stricter bronze schema validation helpers, loaded 137,483 player-file rows to `tennis.bronze_players`, built 5 silver dbt views, and passed 26 dbt data tests. |
| 2026-09-02 | Gold features and baseline prediction completed | Built `tennis.gold_match_features_asof` for 1,538,049 post-1990 matches with 0 future-feature violations, evaluated ranking/Elo/surface-Elo/logistic baselines, and persisted 8 backtest metric rows. |
| 2026-09-02 | Feature leakage gates added | Added Python and dbt checks for feature timing, unique oriented match-feature grain, self-match rows, rank/as-of null consistency, and all joined difference features before model evaluation. The gate found and removed 7 invalid self-match gold rows, leaving 1,538,042 current gold feature rows. |
| 2026-09-03 | Initial prediction diagnostics completed | Added and ran calibration, missingness, and segmented backtest diagnostics; this initial run was superseded by the orientation/calibration rebuild later the same day. |
| 2026-09-03 | Orientation, calibration, and blended surface Elo completed | Rebuilt gold match features with hash-based player orientation independent of player IDs, switched production surface Elo features to sparse-surface shrinkage toward overall Elo, added validation-fitted Platt calibration, reran leakage checks, persisted 12 backtest rows, 120 calibration rows, 648 missingness rows, and 272 segment rows. |
| 2026-09-07 | Source composition, article, and walk-forward evaluation completed | Added source-composition diagnostics for high-performing segments, persisted 50 source-composition rows, added 2016-2025 walk-forward evaluation with 80 persisted rows, and drafted the first public non-commercial article plus companion notebook. |
| 2026-09-09 | Publication hardening completed | Added model-card documentation, held-out isotonic calibration, event/source-level diagnostic flags, publication review docs, refreshed warehouse outputs, and persisted 16 baseline rows, 160 calibration rows, 1,164 segment rows, 159 source-composition rows, and 120 walk-forward rows. |

---

## Open Questions

1. What is the first publishable artifact: Elo leaderboard critique, surface matchup analysis, serve/return decomposition, or match simulator?
2. Should this live as one standalone repo or inside a broader `sports-sabermetrics` monorepo?
3. Will public outputs include only aggregate charts, or also small derived tables?
4. Should the long-term commercial offering target coaches, recreational players, journalists, bettors, fantasy/prediction audiences, or tennis clubs?
5. How should Alex collect original recreational-player match/charting data to support commercial analysis without third-party restrictions?
6. Should model outputs avoid betting-specific framing to keep the project coaching/analytics-oriented?
7. Which official/commercial feeds are affordable enough for a future paid offering?

---

## Known Issues and Gotchas

- Non-commercial data licenses are the central constraint. A portfolio/research project is acceptable; paid deliverables based directly on CC BY-NC-SA sources are not acceptable without permission.
- Forked repos may not preserve license files clearly. Use canonical sources where possible.
- Tennis match statistics are not available uniformly across eras, tours, genders, levels, and surfaces.
- Rankings are time-dependent. Any feature based on ranking, Elo, or form must be computed as-of the match date.
- Random train/test splits are invalid for match prediction. Use temporal splits.
- A player can appear under multiple names, spellings, or IDs across datasets.
- Grand Slam point data has inconsistent columns across tournaments and years.
- Match Charting Project data is rich but not representative of all tennis matches; charted matches are selected by contributors.
- Betting odds are a useful benchmark but may introduce legal/terms-of-use and product-positioning concerns.
- Commercial feeds may have strong redistribution restrictions even when they permit analysis.

---

## Current Priorities

1. Run final human editorial review and publish the non-commercial article with the exported SVGs.
2. Contact TDI/Sportradar/Stats Perform for commercial terms before any paid Savepoint deliverable.
3. Add a legally reviewed, isolated odds baseline only if source terms allow it.
4. Promote source-event mapping into a documented warehouse contract if future marts consume it directly.
5. Add model artifact/version tracking once experiments move beyond transparent baselines.

## Match Prediction And Analytics Feasibility

Assessment date: 2026-08-25.

Descriptive analytics is possible now for non-commercial research and portfolio outputs. The current PostgreSQL silver layer contains:

- `tennis.silver_matches`: 1,762,930 rows, with ATP coverage from 1877-07-09 to 2026-06-01 and WTA coverage from 1967-12-25 to 2026-06-02.
- `tennis.silver_players`: 137,483 rows from ATP/WTA player files.
- `tennis.silver_rankings`: 5,574,677 rows, with ATP rankings from 1973-08-27 to 2026-06-08 and WTA rankings from 1984-01-02 to 2026-06-08.
- `tennis.silver_match_stats`: 3,525,860 player-match stat rows, with serve/break statistic coverage strongest in the modern era.

Match prediction is feasible as the next implementation step, but it should be treated as baseline research until gold feature marts and backtests exist. The data supports no-lookahead Elo, ranking-based, surface-based, and serve/return models. The immediate blocker is not data availability; it is creating strict as-of feature joins and temporal evaluation artifacts so the model cannot use future information.

Update on 2026-09-02: baseline match prediction is implemented for research use. The post-1990 gold feature table has 1,538,042 rows from 1990-01-01 to 2026-06-02, 1,280,284 rows with both player rankings available, 0 rows where `max_feature_asof_date >= match_date`, and 0 self-match rows after leakage gates removed 7 invalid rows.

Update on 2026-09-03: hash-based player orientation, blended surface Elo shrinkage, and validation-fitted Platt calibration are implemented. The current gold feature table has a `player_a_won` rate of 0.499856, which removes the prior side-orientation bias risk while keeping one row per match.

Current 2022-onward test metrics:

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

Update on 2026-09-03: diagnostics are implemented and persisted. The largest logistic-baseline test calibration errors are now in the tails: the 0.9314 mean-prediction bin has a 0.9123 observed win rate, and the 0.0684 mean-prediction bin has a 0.0869 observed win rate.

Update on 2026-09-07: source-composition diagnostics and walk-forward backtests are implemented. The top high-performing missing-rank 2020s test segments are 100% from `aneeshers_tennis_sackmann_archive`, so they should be treated as source-composition findings until event/source mix is reviewed. Across 2016-2025 walk-forward windows, the logistic baseline averages 0.586946 log loss, 0.201187 Brier score, 0.754366 ROC-AUC, and 0.685356 accuracy over 550,657 annual test rows.

Update on 2026-09-09: model-card documentation, held-out isotonic calibration, event/source diagnostic flags, and final publication review docs are implemented. Current output counts are 160 calibration rows, 648 missingness rows, 1,164 segment backtest rows, 159 source-composition rows, and 120 walk-forward rows. The gold feature table now carries `tournament_level` and `draw_size` on all 1,538,042 rows. Isotonic calibration is fit on validation rows only and evaluated on held-out test rows only; it improves the ranking-only baseline and the logistic worst-bin calibration error, but does not beat the uncalibrated logistic baseline on test log loss.

Update on 2026-09-09: walk-forward evaluation now uses precomputed arrays plus a narrow PostgreSQL feature loader after SQL leakage gates pass. Full 2016-2025 PostgreSQL-backed refresh time dropped from 141.66 seconds to 74.29 seconds in the local environment. Event-level mapping now uses Sackmann-derived code semantics for ITF numeric prize levels, ATP satellites/ITFs, season finals, team cups, and Olympics; persisted segment rows no longer include `event_level = unknown`. Article/notebook caption notes and the commercial data path are documented.

Update on 2026-09-09: diagnostics now use a narrow PostgreSQL feature loader after SQL leakage gates pass, cache the model-ready diagnostics extract with snapshot metadata under ignored `outputs/cache/`, write `match_event_level_mapping.csv`, persist `tennis.gold_event_level_mapping_diagnostics`, and support `--fail-on-unmapped-events`. The hard-gated refresh completed with 38 mapping rows and 0 unmapped source rows; the uncached run took 113.45 seconds and a cached no-persist repeat took 77.26 seconds. Static article SVGs plus captions were exported to ignored `outputs/charts/article/`.

Update on 2026-09-28: the match-prediction article has been rewritten as a publication-ready non-commercial post with embedded static SVG references, captions, caveats, and reproducibility commands. dbt now includes source-event validation tests for unmapped `gold_match_features_asof` tournament codes and persisted event-mapping diagnostics. Baseline and walk-forward PostgreSQL evaluations now reuse snapshot-aware feature caches under ignored `outputs/cache/`, matching the diagnostics cache pattern while preserving SQL leakage gates. Verified cache-populating no-persist runtimes were 307.73 seconds for baseline evaluation and 85.30 seconds for walk-forward evaluation.

Important caveats:

- Current source data is CC BY-NC-SA and should not be used for paid deliverables without permission or a commercial license.
- Silver match views exclude rows without parsed match date, winner ID, or loser ID; doubles files are preserved in bronze but are outside the current singles schema contract.
- Player identity normalization is source-ID based and still needs cross-source deduplication before combining additional datasets.
- Betting odds are not loaded and should remain isolated until terms are verified.
- Public outputs need attribution, snapshot date, sample size, time period, tours, surface filters, missingness caveats, and non-commercial caveats.

---

## Cross-Vertical Connections

| Tennis project | Connects to | How |
|---|---|---|
| Player archetypes | Game analytics segmentation | Same clustering pipeline with different behavioral features. |
| Match outcome prediction | Game churn/retention modeling | Same temporal validation and leakage-avoidance discipline. |
| Point-state win probability | Game economy simulation / board game AI | Sequential state model with probabilistic transitions. |
| Counterfactual improvement simulation | Product experimentation | Similar to uplift/counterfactual reasoning. |
| Surface adaptation | Domain shift / live game balance patches | Same problem of performance under changed environment. |
| Coaching-facing outputs | Savepoint dashboarding | Same need for clear operational metrics, not decorative BI. |

---

## Files That Should Exist Near This File

```text
CLAUDE.md
COMPANY_CONTEXT.md
PROJECT_CONTEXT.md
AGENTS.md
registry.md
public-data-sources.md
README.md
data/
docs/
src/
dbt/
flows/
tests/
```

---

## Next Review Date

Review this document after:
- The initial repo scaffold is committed.
- ATP/WTA match data is ingested.
- The first Elo baseline is evaluated.
- A major data source or license decision changes.
- A commercial data-source path is identified.
