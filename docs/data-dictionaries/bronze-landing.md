# Bronze Landing Tables

Bronze landing tables live in PostgreSQL schema `tennis` and are loaded from local bronze Parquet outputs.

The loader is:

```bash
uv run tennis-sabermetrics load-bronze-postgres \
  --bronze-root .local/bronze \
  --snapshot-date 2026-08-25
```

Current fallback snapshot:

- Source key: `aneeshers_tennis_sackmann_archive`
- Snapshot date: `2026-08-25`
- Source commit: `83733587353df8a41f2fd4f516147d5aa83f5a8d`

## Tables

| Table | Purpose | Current row count |
|---|---|---:|
| `tennis.bronze_matches` | Match-level rows from ATP/WTA match CSVs. | 1,801,272 |
| `tennis.bronze_rankings` | Headerless ranking rows normalized from source columns `0..3`. | 5,574,926 |
| `tennis.bronze_players` | Player rows loaded from ATP/WTA player CSVs, with match-participant derivation retained only as a loader fallback. | 137,483 |
| `tennis.bronze_tournaments` | Tournament rows derived from match files. | 69,592 |
| `tennis.bronze_match_stats` | One winner and one loser stat row per match. | 3,602,544 |

## Notes

- Bronze values are still source-shaped and conservative. Most fields are text or direct casts.
- `match_id` is derived as `<tour>:<tourney_id>:<match_num>`.
- Player rows now prefer dedicated player files. If player-file bronze outputs are absent for a source, the PostgreSQL loader falls back to deriving players from match participants.
- Current bronze schema validation checks required columns for players, matches, and rankings, and parseable date columns for eligible singles match and ranking files. Doubles match files are preserved in bronze but are outside the current singles match schema contract.
- Match-stat rows compute second-serve point totals as service points minus first serves in.
- Raw and bronze third-party artifacts remain outside Git under ignored `.local/` paths and MinIO.
