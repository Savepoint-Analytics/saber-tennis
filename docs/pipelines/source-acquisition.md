# Source Acquisition Pipeline

The first acquisition pipeline must be metadata-first.

## Required Behavior

`tennis-sabermetrics sync-sources --dry-run` lists canonical sources and their license metadata without downloading data.

The CLI loads `.env` automatically. For PostgreSQL it accepts `POSTGRES_*`, `SAVEPOINT_PG_*`, and `POSTGRESQL_DB_*` variable names. For MinIO it accepts `MINIO_*`, `SAVEPOINT_MINIO_*`, and AWS-style access key aliases. If `MINIO_ENDPOINT` points at `MINIO_CONSOLE_PORT` and `MINIO_PORT` is set, the endpoint is normalized to the S3 API port.

Non-dry-run source sync now:

1. Clone or fetch canonical repositories into `EXTERNAL_REPOS_ROOT`.
2. Record commit SHA.
3. Generate SHA256 checksums for every source file.
4. Skip repository internals such as `.git`.
5. Refuse missing license metadata unless explicitly isolated.

With explicit flags, source sync can also:

1. Copy raw files to MinIO under `raw/<source>/snapshot_date=<date>/commit=<sha>/`.
2. Write manifest rows for each file.

Example:

```bash
uv run tennis-sabermetrics sync-sources \
  --source jeffsackmann_tennis_atp \
  --snapshot-date 2026-07-15 \
  --copy-raw-to-minio \
  --write-raw-manifest
```

`--write-raw-manifest` requires `--copy-raw-to-minio` so manifest rows point at actual immutable raw storage.

The command validates MinIO access key and secret key before cloning/fetching when raw copy is requested.

Operational status as of 2026-08-25:

- PostgreSQL metadata tables are bootstrapped and reachable.
- MinIO bucket access is reachable through the normalized S3 API endpoint.
- ATP/WTA canonical GitHub acquisition is blocked because the configured canonical repositories returned 404.
- `Aneeshers/tennis-sackmann-archive` is reviewed and implemented as a fallback source under CC BY-NC-SA constraints, but the canonical ATP/WTA source keys are not remapped to it.
- Fallback ATP/WTA raw snapshot `2026-08-25` has 302 PostgreSQL manifest rows and raw files copied to MinIO.

See [source-availability.md](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/pipelines/source-availability.md) for the current source decision record.

## Fallback Handling

Fallback archive ingestion must be explicit. Do not change `jeffsackmann_tennis_atp` or `jeffsackmann_tennis_wta` to point at a mirror. Use a distinct fallback source key, record the mirror commit, preserve original Jeff Sackmann attribution, and keep the non-commercial/share-alike flags in metadata.

Fallback ATP/WTA sync examples:

```bash
uv run tennis-sabermetrics sync-sources \
  --source aneeshers_tennis_sackmann_archive \
  --source-subdir atp \
  --snapshot-date 2026-08-25 \
  --external-repos-root .local/external \
  --copy-raw-to-minio \
  --write-raw-manifest

uv run tennis-sabermetrics sync-sources \
  --source aneeshers_tennis_sackmann_archive \
  --source-subdir wta \
  --snapshot-date 2026-08-25 \
  --external-repos-root .local/external \
  --copy-raw-to-minio \
  --write-raw-manifest
```

## Storage

Raw data is immutable and should not be modified in place. Bronze data should preserve source-shaped columns and add metadata fields such as `_source_key`, `_source_url`, `_source_commit_sha`, `_snapshot_date`, `_ingested_at`, and `_license_name`.

The initial bronze helper is `convert_csv_to_bronze_parquet`, which takes a CSV path, Parquet path, and explicit `BronzeMetadata`.

ATP/WTA bronze batches are available through:

```bash
uv run tennis-sabermetrics build-bronze \
  --source jeffsackmann_tennis_atp \
  --snapshot-date 2026-07-15 \
  --source-commit-sha <commit>
```

Fallback archive bronze batches require an explicit tour:

```bash
uv run tennis-sabermetrics build-bronze \
  --source aneeshers_tennis_sackmann_archive \
  --archive-tour atp \
  --snapshot-date 2026-08-25 \
  --source-root .local/external/tennis-sackmann-archive \
  --bronze-root .local/bronze \
  --source-commit-sha 83733587353df8a41f2fd4f516147d5aa83f5a8d
```

Bronze output defaults to `BRONZE_DATA_ROOT`, not the Git-tracked `data/` directory.

In this local workspace, `/mnt/data` is not writable, so the fallback run used ignored `.local/external` and `.local/bronze` paths.

## PostgreSQL Bronze Load

Load local bronze Parquet into PostgreSQL landing tables:

```bash
uv run tennis-sabermetrics load-bronze-postgres \
  --bronze-root .local/bronze \
  --snapshot-date 2026-08-25
```

Verified load counts for snapshot `2026-08-25`:

- `tennis.bronze_matches`: 1,801,272
- `tennis.bronze_rankings`: 5,574,926
- `tennis.bronze_players`: 137,483
- `tennis.bronze_tournaments`: 69,592
- `tennis.bronze_match_stats`: 3,602,544

`tennis.bronze_players` now prefers dedicated ATP/WTA player files. If those bronze files are absent for a source, the loader falls back to deriving players from match participants.

Enrich raw manifest row counts from local raw files:

```bash
uv run tennis-sabermetrics enrich-raw-manifest-row-counts \
  --source-root .local/external/tennis-sackmann-archive \
  --snapshot-date 2026-08-25
```

Current result: 299 tabular files updated, 3 non-CSV files left null.
