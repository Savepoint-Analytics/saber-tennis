# PROJECT_CONTEXT.md — Sports Sabermetrics — Tennis Empirical Analysis

_Last updated: 2026-06-29_

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

**Current focus:** Use the metadata-first scaffold to bootstrap `source_license` / `raw_manifest`, dry-run canonical source sync, then add ATP/WTA bronze conversion without committing raw data.

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

1. Install/sync local Python tooling with `uv` and run the full `ruff` / `pytest` suite.
2. Bootstrap `tennis.source_license` and `tennis.raw_manifest` with `scripts/bootstrap_postgres.sql`.
3. Extend the source sync script from dry-run planning to clone/fetch, commit SHA capture, checksum generation, and MinIO copy.
4. Build ATP/WTA match and ranking bronze Parquet conversion with metadata columns.
5. Expand score parser coverage for retirements, walkovers, super-tiebreaks, Davis Cup/team events, and old scoring conventions.
6. Implement surface Elo with strict as-of-date evaluation.
7. Produce a first public notebook: “Why Elo and serve/return decomposition beat raw rankings for tennis analysis.”

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
