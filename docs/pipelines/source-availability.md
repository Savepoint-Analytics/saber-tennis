# Source Availability Decision Record

_Last updated: 2026-08-25_

## Current Finding

Canonical ATP and WTA acquisition is still blocked. Local checks on 2026-08-24 returned repository-not-found responses for:

- `https://github.com/JeffSackmann/tennis_atp`
- `https://github.com/JeffSackmann/tennis_wta`

Jeff Sackmann's public GitHub profile currently exposes `tennis_MatchChartingProject`, but not ATP/WTA as public repositories. `tennis_MatchChartingProject` remains reachable; local `git ls-remote` returned HEAD `2c59eef194967e688b69e73df344184a06322cd8`.

## Reviewed Fallback

`https://github.com/Aneeshers/tennis-sackmann-archive` is a reviewed fallback candidate, not a canonical replacement. It presents itself as an archival mirror of Jeff Sackmann's ATP, WTA, and Grand Slam point-by-point datasets, contains data and documentation only, preserves upstream README files, and states that ATP/WTA snapshots came from upstream commits made in June 2026.

Local availability checks:

- GitHub archive mirror HEAD: `83733587353df8a41f2fd4f516147d5aa83f5a8d`
- Hugging Face archive mirror HEAD: `8ac86f7c62889b5d5c4cfec4c6403edcb8c5d993`

License handling:

- Treat the archive as CC BY-NC-SA 4.0.
- Attribute Jeff Sackmann and link to the original repositories.
- Keep non-commercial and share-alike constraints.
- Record mirror URL, mirror commit, original upstream provenance notes, snapshot date, and file checksums.
- Do not use this fallback for paid Savepoint Analytics outputs without written permission or commercial data rights.

## Decision

Keep `jeffsackmann_tennis_atp` and `jeffsackmann_tennis_wta` as canonical source keys. Add `aneeshers_tennis_sackmann_archive` as a metadata-tracked fallback source, but do not silently remap canonical source keys to the mirror.

## Execution Status

Fallback ATP and WTA raw snapshots were synced on 2026-08-25 from archive commit `83733587353df8a41f2fd4f516147d5aa83f5a8d`.

Results:

- `atp/`: 176 files copied to MinIO and registered in `tennis.raw_manifest`.
- `wta/`: 126 files copied to MinIO and registered in `tennis.raw_manifest`.
- Total fallback manifest rows for snapshot date `2026-08-25`: 302.
- ATP bronze Parquet files built locally under ignored `.local/bronze`: 174.
- WTA bronze Parquet files built locally under ignored `.local/bronze`: 125.
- PostgreSQL bronze landing tables loaded from local bronze Parquet, including dedicated ATP/WTA player files.
- dbt staging and silver views built in PostgreSQL.
- Raw manifest row counts enriched for 299 CSV files; 3 non-CSV files remain null.

Raw data and bronze Parquet outputs remain outside Git.
