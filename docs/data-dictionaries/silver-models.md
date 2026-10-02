# Silver dbt Models

Silver models live in PostgreSQL schema `tennis` as dbt views. They normalize the bronze landing tables enough for analytics and leakage-safe feature work.

Verified snapshot:

- Source key: `aneeshers_tennis_sackmann_archive`
- Snapshot date: `2026-08-25`
- Source commit: `83733587353df8a41f2fd4f516147d5aa83f5a8d`

## Models

| Model | Purpose | Current row count |
|---|---|---:|
| `tennis.silver_players` | Distinct ATP/WTA player identities and profile fields from player files. | 137,483 |
| `tennis.silver_tournaments` | Distinct tournament/date/surface entities derived from match files. | 64,396 |
| `tennis.silver_matches` | Singles match records with non-null date, winner, and loser IDs. | 1,762,930 |
| `tennis.silver_rankings` | Ranking rows with parsed ranking dates and player IDs. | 5,574,677 |
| `tennis.silver_match_stats` | Player-match stat rows for winners and losers. | 3,525,860 |

## Coverage

Current match coverage by tour:

| Tour | Matches | Date range | With surface |
|---|---:|---|---:|
| ATP | 988,216 | 1877-07-09 to 2026-06-01 | 983,587 |
| WTA | 774,714 | 1967-12-25 to 2026-06-02 | 768,521 |

Current post-1990 coverage:

| Tour | Matches since 1990 | With surface |
|---|---:|---:|
| ATP | 861,108 | 861,055 |
| WTA | 676,941 | 676,642 |

Ranking coverage:

| Tour | Ranking rows | Date range | Ranked players |
|---|---:|---|---:|
| ATP | 3,420,414 | 1973-08-27 to 2026-06-08 | 17,033 |
| WTA | 2,154,263 | 1984-01-02 to 2026-06-08 | 9,900 |

Player-match stat coverage:

| Tour | Player-match stat rows | With serve points | With aces | With break points |
|---|---:|---:|---:|---:|
| ATP | 1,976,432 | 519,360 | 519,361 | 519,360 |
| WTA | 1,549,428 | 201,435 | 201,419 | 201,427 |

## Data Quality

The silver layer currently has dbt data tests for required IDs/dates and row-key uniqueness. On 2026-08-25, `dbt run` built 12 staging/silver views and `dbt test` passed 26 data tests.

The silver match layer is suitable for descriptive match, surface, date, tour, ranking, and player analytics. Prediction feature tables should be built as gold marts so every feature is computed as of the match date.
