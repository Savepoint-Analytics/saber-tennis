# Source Acquisition Pipeline

The first acquisition pipeline must be metadata-first.

## Required Behavior

`tennis-sabermetrics sync-sources --dry-run` lists canonical sources and their license metadata without downloading data.

Future non-dry-run behavior should:

1. Clone or fetch canonical repositories into `EXTERNAL_REPOS_ROOT`.
2. Record commit SHA.
3. Generate SHA256 checksums for every source file.
4. Copy raw files to MinIO under `raw/<source>/snapshot_date=<date>/commit=<sha>/`.
5. Write manifest rows for each file.
6. Convert CSVs to bronze Parquet with metadata columns.
7. Refuse missing license metadata unless explicitly isolated.

## Storage

Raw data is immutable and should not be modified in place. Bronze data should preserve source-shaped columns and add metadata fields such as `_source_key`, `_source_url`, `_source_commit_sha`, `_snapshot_date`, `_ingested_at`, and `_license_name`.

