# Raw Manifest Data Dictionary

`tennis.raw_manifest` tracks immutable raw source files after they are copied to MinIO-compatible storage.

| Column | Description |
|---|---|
| `manifest_id` | Surrogate primary key. |
| `source_key` | Foreign key to `tennis.source_license`. |
| `snapshot_date` | Project snapshot date for the source acquisition run. |
| `source_commit_sha` | Git commit SHA when the source is a Git repository. |
| `source_file_path` | Path relative to the source repository or snapshot root. |
| `minio_uri` | Immutable raw object URI, usually `s3://tennis-sabermetrics/raw/...`. |
| `file_sha256` | SHA256 checksum of the raw file bytes. |
| `row_count` | Optional row count when cheaply available. For the 2026-08-25 fallback ATP/WTA snapshot, CSV files are enriched and non-CSV metadata/docs remain null. |
| `acquired_at` | Timestamp when the manifest entry was generated. |
| `acquired_by` | Database user that inserted the row. |
| `notes` | Source-specific caveats or handling notes. |

The unique key is `(source_key, snapshot_date, source_file_path, file_sha256)`, so repeated ingest attempts do not duplicate identical raw files.
