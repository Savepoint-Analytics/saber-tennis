# CLAUDE.md — Tennis Sabermetrics

_Last updated: 2026-06-28_

## Inheritance

This file extends the global Savepoint Analytics context and the Sports Sabermetrics context.
All global rules apply. Rules here take precedence where they conflict.

Related files:
- `COMPANY_CONTEXT.md` — business source of truth.
- `PROJECT_CONTEXT.md` — project history and current working context.
- `registry.md` — dataset registry and acquisition status.
- `public-data-sources.md` — source-specific data and license notes.
- `AGENTS.md` — execution rules for coding agents.

---

## Vertical Identity

**Vertical:** Sports Sabermetrics  
**Sub-vertical:** Tennis  
**Project:** Tennis Empirical Analysis  
**Portfolio goal:** Demonstrate rigorous tennis analytics capability; build public credibility beyond game analytics; create a foundation for future affordable tennis analysis.  
**Audience for outputs:** Tennis coaches, tennis players, sports analytics community, technical hiring managers, sports fans who appreciate data, and future Savepoint Analytics clients.  
**Primary operator:** Alex Oswald / Savepoint Analytics.

---

## Core Mission

Help Alex build a reproducible tennis analytics system that can:

1. Predict match outcomes.
2. Explain why players win or lose.
3. Decompose performance into serve, return, surface, form, pressure, and tactical components.
4. Model the structure of tennis from points to games to sets to matches.
5. Simulate counterfactual improvement scenarios.
6. Produce portfolio-grade public artifacts.
7. Preserve a viable future commercial path without violating data licenses.

---

## Domain Expertise to Apply

### Tennis Structure

- Tennis is hierarchical: **points → games → sets → matches**.
- Never treat match outcome as a flat binary event if the question requires point/game/set mechanics.
- Best-of-three and best-of-five formats have different upset probabilities.
- Tiebreaks need separate handling because serve alternation and leverage differ from regular games.
- Retirements, walkovers, defaults, super-tiebreaks, team events, and format changes must be explicitly flagged.

### Serve and Return Metrics

Default serve metrics:
- First-serve percentage.
- First-serve points won.
- Second-serve points won.
- Ace rate per service point.
- Double-fault rate per service point.
- Service points won.
- Hold percentage.
- Break points saved, with sample-size caveats.

Default return metrics:
- Return points won.
- First-serve return points won.
- Second-serve return points won.
- Break percentage.
- Break point conversion, with sample-size caveats.
- Return depth, return direction, and return-in-play rate when charted data supports it.

Always separate serve skill from return skill when explaining performance.

### Surface Adjustments

- Hard, clay, grass, and indoor conditions materially change player performance.
- Surface-adjusted metrics are preferred over all-surface aggregate metrics.
- Surface-specific Elo and serve/return stats should be default context for match prediction.
- Beware small samples on grass and indoor surfaces.
- Do not assume a player’s hard-court profile transfers directly to clay or grass.

### Elo and Rating Systems

- Elo-based systems are usually more predictive than official ATP/WTA rankings because opponent strength matters.
- Maintain separate or blended ratings for:
  - Overall Elo.
  - Surface Elo.
  - Serve Elo / return Elo if supported.
  - Recent-form Elo or time-decayed variants.
- Always compute ratings **as of match date**. No future results may leak into a prediction row.
- Treat Tennis Abstract Elo as a benchmark/reference, not a source to copy blindly.

### Point-Level and Shot-Level Analysis

When point or charting data is available, analyze:
- Server vs returner point win probability.
- Rally length.
- Serve direction and depth.
- Return depth and return in play.
- Winner / unforced error / forced error split.
- Net approaches and serve-and-volley patterns.
- Break points, deuce/ad, set points, match points, and tiebreak leverage.

Always flag charting coverage bias: charted matches are not a random sample of all tennis.

### Counterfactual Simulation

Counterfactuals should be structured as:

> If Player A improves component X by Y amount, holding other components constant, expected game/set/match win probability changes by Z.

Good counterfactuals:
- Improve second-serve points won by 2 percentage points.
- Reduce double-fault rate by 1 point per 100 service points.
- Increase return-in-play rate against first serves.
- Improve break-point performance only after accounting for underlying return strength.
- Shift surface mix or match format.

Bad counterfactuals:
- “What if the player became more clutch?” without defining a measurable component.
- “What if they tried harder?”
- Causal claims from observational differences without a model and caveats.

---

## Statistical and Modeling Standards

### Always Do

- Report sample size with every rate.
- State time period and surface context.
- Use confidence intervals or uncertainty bands for published rates.
- Use strict temporal splits for prediction.
- Compute rolling/form features using only past matches.
- Benchmark models against simple baselines: ranking, Elo, surface Elo, betting odds if legally available.
- Evaluate probability calibration, not only accuracy.
- Report log loss and Brier score for probabilistic predictions.
- Distinguish descriptive findings from predictive findings and causal claims.
- State known missingness or selection bias.

### Never Do

- Use random train/test splits for match prediction.
- Let future rankings, future Elo, future form, tournament outcome, or final match stats leak into pre-match predictions.
- Rank players by raw wins without adjusting for schedule strength, surface, era, and match volume.
- Treat break point conversion as “clutch” without accounting for return skill and sample size.
- Treat head-to-head records as decisive when samples are small or surface/context differs.
- Use non-commercial datasets in paid deliverables without permission.
- Copy unlicensed GitHub code.
- Redistribute third-party raw data unless the license explicitly allows it.

---

## Leakage Rules

Any pre-match feature must be available before the match starts.

Forbidden for pre-match rows:
- Match result.
- Final score-derived stats.
- Post-match ranking updates.
- Post-match Elo updates.
- Tournament round reached after the match.
- Season-end or future rolling averages.
- Opponent form that includes the current/future match.

Required tests:
- `test_elo_no_lookahead.py`
- `test_temporal_split.py`
- `test_asof_features.py`
- `test_no_future_rankings.py`

---

## Licensing and Data Use Rules

### Core Rule

Treat licensing as part of correctness. A technically correct answer that violates license constraints is not acceptable.

### Jeff Sackmann / Tennis Abstract Sources

The main Tennis Abstract / Jeff Sackmann datasets and algorithms should be treated as **CC BY-NC-SA 4.0** unless a specific source says otherwise.

Implications:
- Attribution required.
- Non-commercial use only.
- Share-alike obligations may apply to derivatives.
- Public portfolio research is acceptable when properly attributed and non-commercial.
- Paid client work, commercial dashboards, subscriptions, betting products, or resold datasets require separate permission or a different licensed data source.

### Forked Repositories

The user listed several forks or non-canonical repository URLs. Prefer canonical JeffSackmann sources when possible:

- Prefer `JeffSackmann/tennis_atp` over forks such as `oz-tmg/tennis_atp`.
- Prefer `JeffSackmann/tennis_wta` over forks such as `ppaulojr/tennis_wta`.
- Prefer `JeffSackmann/tennis_slam_pointbypoint` over older forks such as `halepmania/tennis_slam_pointbypoint`.
- Prefer `JeffSackmann/tennis_pointbypoint` over forks such as `ppaulojr/tennis_pointbypoint`.
- Prefer `JeffSackmann/tennis_misc` over forks such as `halepmania/tennis_misc`.
- Prefer `JeffSackmann/tennis_viz` over forks such as `satya469/tennis_viz`.

If a fork has no explicit license, do not copy its code. Use it only for source discovery or methodology inspiration unless licensing is clarified.

### Commercialization Rule

Before any paid Savepoint Analytics tennis offering, require one of:

1. Written commercial permission from data owner.
2. Licensed commercial feed.
3. Client-supplied data with rights to analyze it.
4. Original Savepoint-collected data.
5. Public-domain/open-commercial data whose terms are verified.

---

## Preferred Data Architecture

Use Savepoint-Lab as the development backend.

- **MinIO:** immutable raw and bronze snapshots.
- **PostgreSQL:** normalized relational tennis schema and dbt marts.
- **DuckDB:** fast local exploration over Parquet.
- **Prefect:** ingestion and transformation orchestration.
- **dbt:** staging/intermediate/mart models.
- **MLflow:** experiment tracking and model artifacts.
- **Git:** code, docs, schemas, tests, and tiny fixtures only.

Recommended PostgreSQL schema: `tennis`.

Recommended MinIO bucket: `tennis-sabermetrics`.

---

## Preferred Python Stack

Use Python first.

```text
uv
pandas
polars
numpy
duckdb
pyarrow
sqlalchemy
psycopg
pydantic
pandera
scikit-learn
xgboost
lightgbm
statsmodels
scipy
optuna
mlflow
plotly
dash
typer
rich
pytest
ruff
mypy
```

Use R sparingly for:
- Validating against existing R tennis examples.
- One-off statistical reports.
- Reproducing R-based approaches before porting them to Python.

---

## Recommended Build Sequence

1. Repository scaffold and context files.
2. `source_license` and `raw_manifest` metadata tables.
3. Source sync script for GitHub CSV repos.
4. ATP/WTA match and ranking ingestion.
5. Score parser and match normalization tests.
6. Baseline Elo and surface Elo.
7. Serve/return decomposition marts.
8. Strict temporal backtest framework.
9. Match outcome model baseline.
10. Point/game/set/match simulator.
11. Counterfactual simulator.
12. Dash/Plotly public dashboard.

---

## First Publishable Artifact Recommendation

Build:

> “Surface-adjusted Elo plus serve/return decomposition: a transparent baseline for tennis match prediction.”

Minimum content:
- ATP and WTA examples.
- Surface-specific performance.
- Official ranking vs Elo comparison.
- Serve/return components.
- Temporal backtest with log loss, Brier score, calibration curve.
- Plain-language coaching implications.
- Clear license attribution.

---

## Output Standards

Every public notebook, article, chart, or dashboard must include:

- Data source and download/snapshot date.
- License attribution.
- Time period covered.
- Tours and levels covered.
- Surface filters.
- Sample size.
- Missingness caveats.
- Whether findings are descriptive, predictive, or causal.
- Model evaluation period when predictions are shown.

---

## AI Behavior Rules

When assisting on this project:

- Be implementation-ready.
- Do not hand-wave around licensing.
- Prefer small tested modules over giant notebooks.
- Prefer clear baselines before complex ML.
- Surface leakage risks aggressively.
- Push for reproducibility: manifests, snapshots, checksums, tests.
- Keep the coaching interpretation in view.
- Do not frame outputs as gambling advice.
- When unsure about a source’s license or terms, say so and recommend isolation/private evaluation only.

---

## Attribution Template

Use this or an equivalent attribution in public outputs that rely on Tennis Abstract / Jeff Sackmann data:

> Data derived from Jeff Sackmann / Tennis Abstract repositories, including Tennis Abstract ATP/WTA results, rankings, point-by-point data, and/or the Match Charting Project. Original sources are licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International unless otherwise stated. This project is a non-commercial research/portfolio use and does not redistribute raw third-party data.

---

## Update Log

| Date | Update |
|---|---|
| 2026-06-28 | Created tennis-specific Claude guidance covering domain rules, leakage prevention, storage, stack, and licensing constraints. |
