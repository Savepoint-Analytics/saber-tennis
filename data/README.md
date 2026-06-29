# Data Directory

This directory is for documentation, metadata, and tiny license-safe fixtures only.

Allowed in Git:

- Synthetic fixtures created for tests.
- Small metadata files such as source license seeds.
- README files explaining external data locations.

Not allowed in Git:

- Bulk Tennis Abstract / Jeff Sackmann raw CSVs.
- Raw point-by-point, charting, odds, or ranking snapshots.
- Generated bronze/silver/gold datasets.

Raw and bronze snapshots should be stored in MinIO under the `tennis-sabermetrics` bucket with source URL, commit/date, license, snapshot date, and checksums recorded in the manifest.

