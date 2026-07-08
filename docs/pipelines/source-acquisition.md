# Source Acquisition Pipeline

The first acquisition pipeline must be metadata-first.

## Required Behavior

`tennis-sabermetrics sync-sources --dry-run` lists canonical sources and their license metadata without downloading data.

Non-dry-run source sync now:

1. Clone or fetch canonical repositories into `EXTERNAL_REPOS_ROOT`.
2. Record commit SHA.
3. Generate SHA256 checksums for every source file.
4. Skip repository internals such as `.git`.
5. Refuse missing license metadata unless explicitly isolated.

Future source sync adapters should:

1. Copy raw files to MinIO under `raw/<source>/snapshot_date=<date>/commit=<sha>/`.
2. Write manifest rows for each file.
3. Convert source CSVs to bronze Parquet with metadata columns.

## Storage

Raw data is immutable and should not be modified in place. Bronze data should preserve source-shaped columns and add metadata fields such as `_source_key`, `_source_url`, `_source_commit_sha`, `_snapshot_date`, `_ingested_at`, and `_license_name`.

The initial bronze helper is `convert_csv_to_bronze_parquet`, which takes a CSV path, Parquet path, and explicit `BronzeMetadata`.
