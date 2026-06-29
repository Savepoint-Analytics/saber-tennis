# Project Layout

The repository is organized around a small reusable Python package, metadata-first ingestion, and docs that make licensing and leakage constraints visible.

## Core Paths

| Path | Purpose |
|---|---|
| `src/tennis_sabermetrics/` | Reusable Python package for ingestion, transforms, features, models, simulations, evaluation, and visualization. |
| `tests/` | Fast tests for parsing, temporal validation, no-lookahead behavior, and metadata guardrails. |
| `data/` | Metadata and tiny synthetic fixtures only. No bulk third-party raw data. |
| `dbt/` | Future PostgreSQL staging, intermediate, and mart models. |
| `flows/` | Future Prefect orchestration wrappers. |
| `scripts/` | Bootstrap and operational scripts. |
| `docs/` | Methodology, data dictionaries, licensing, and pipeline documentation. |
| `outputs/` | Local generated charts/tables/reports. Ignored by Git except placeholder files. |

## Package Layout

| Module | Responsibility |
|---|---|
| `config.py` | Source keys, project paths, and license metadata. |
| `ingest/` | Source sync planning and checksum manifests. |
| `transform/` | Score, point, player, match, and surface normalization. |
| `features/` | As-of-date features, rolling form, serve/return, head-to-head, and pressure metrics. |
| `models/` | Elo, match outcome, point win probability, and calibration models. |
| `simulation/` | Game/set/match/counterfactual simulation. |
| `evaluation/` | Temporal splits, metrics, baselines, and leakage checks. |
| `viz/` | Plotly/Dash helpers for public artifacts. |

