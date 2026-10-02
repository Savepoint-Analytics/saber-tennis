# dbt Transformations

This dbt project targets PostgreSQL schema `tennis`.

Use the repo-local profile:

```bash
set -a
source ../.env
set +a
UV_CACHE_DIR=../.uv-cache uv run dbt debug --profiles-dir .
UV_CACHE_DIR=../.uv-cache uv run dbt run --profiles-dir .
UV_CACHE_DIR=../.uv-cache uv run dbt test --profiles-dir .
```

`profiles.yml` reads environment variables only and does not contain secrets.

Verified on 2026-09-28:

- `dbt debug` passed.
- `dbt run` built 12 staging and silver views in schema `tennis`.
- `dbt test` passed 31 data tests, including 3 gold feature leakage tests and 2 source-event validation tests.

Current staging coverage:

- `stg_source_license`
- `stg_raw_manifest`
- `stg_players`
- `stg_tournaments`
- `stg_matches`
- `stg_rankings`
- `stg_match_stats`

Current silver coverage:

- `silver_players`
- `silver_tournaments`
- `silver_matches`
- `silver_rankings`
- `silver_match_stats`

`stg_source_license` and `stg_raw_manifest` read from the metadata tables created by `scripts/bootstrap_postgres.sql`.

The player, tournament, match, ranking, and match-stat staging models read from PostgreSQL bronze landing tables loaded by `tennis-sabermetrics load-bronze-postgres`. They still compile to empty typed views if those landing tables are absent, so metadata-only dbt work remains possible.

Silver models are conservative normalized views over staging. The current `tennis.gold_match_features_asof` table is built by Python because Elo, form, rest, and serve/return features require ordered state updates.

Gold leakage tests:

- `gold_match_features_no_future_dates`
- `gold_match_features_unique_grain`
- `gold_match_features_difference_columns_consistent`

Gold source-event validation tests:

- `gold_match_features_event_codes_mapped`
- `gold_event_level_mapping_no_unmapped_rows`

Future dbt work should focus on calibration marts and simple aggregations over the gold tables.

Bronze landing tables:

- `tennis.bronze_players`
- `tennis.bronze_tournaments`
- `tennis.bronze_matches`
- `tennis.bronze_rankings`
- `tennis.bronze_match_stats`

Raw and bronze Parquet files remain outside Git.
