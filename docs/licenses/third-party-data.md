# Third-Party Data Licensing

Licensing is part of project correctness. A model or chart that violates source terms is not acceptable, even if it is technically accurate.

## Default Source Policy

Treat Jeff Sackmann / Tennis Abstract sources as CC BY-NC-SA 4.0 unless a source-specific license says otherwise:

- `JeffSackmann/tennis_atp`
- `JeffSackmann/tennis_wta`
- `JeffSackmann/tennis_MatchChartingProject`
- `JeffSackmann/tennis_slam_pointbypoint`
- `JeffSackmann/tennis_pointbypoint`
- `JeffSackmann/tennis_misc`
- Tennis Abstract Elo pages

Implications:

- Public non-commercial research and portfolio artifacts are allowed with attribution.
- Paid Savepoint Analytics deliverables are not allowed from these datasets without permission or a commercial license.
- Raw data should live outside Git in MinIO or an equivalent external store.
- Public derived tables must be reviewed to ensure they do not effectively republish restricted raw data.

## Unverified Or Isolated Sources

Sources with unclear terms, such as Tennis-Data.co.uk or TML-Database, must be isolated from default public marts and commercial workflows until their terms are reviewed.

## Required Metadata

Every source snapshot must record:

- Source key.
- Source URL.
- Source commit or snapshot date.
- License name and URL where available.
- Snapshot date.
- File checksums.
- Storage URI.
- Attribution and commercial-use flags.

