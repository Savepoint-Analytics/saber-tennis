# Event-Level Mapping

Last updated: 2026-09-09.

The prediction diagnostics map source tournament codes into coarse event classes so missing-rank performance can be separated by event mix.

## Sackmann-Derived ATP/WTA Codes

Source basis: the upstream `matches_data_dictionary.txt` in the reviewed `aneeshers_tennis_sackmann_archive` fallback mirror.

| Source code | Tour context | Diagnostic event level | Notes |
|---|---|---|---|
| `G` | ATP/WTA | `grand_slam` | Grand Slam events. |
| `M` | ATP | `tour_level` | Masters 1000. |
| `A` | ATP | `tour_level` | Other tour-level ATP events. |
| `P`, `PM`, `P5`, `I`, `W` | WTA | `tour_level` | WTA tour-level codes, including Premier and International-era labels. |
| `T1` through `T5` | WTA | `tour_level` | Older WTA tier designations. |
| `C` | ATP/WTA | `challenger_level` | Challenger or circuit-level source code. |
| `S` | ATP | `itf_level` | Satellite/ITF source code. |
| Numeric values such as `10`, `15`, `25`, `50`, `100` | ATP/WTA fallback archive | `itf_level` | Interpreted as ITF prize-money levels in thousands. |
| Numeric `+H` values such as `50+H` | ATP/WTA fallback archive | `itf_level` | Hospitality variant of ITF prize-money code. |
| `CC` | WTA fallback archive | `itf_level` | Circuit-level events; current bronze names are circuit tournaments with 10K/40K prize levels. |
| `F` | ATP/WTA | `season_final` | Season-ending finals or similar events. |
| `D` | ATP/WTA | `team_cup` | Davis Cup, Billie Jean King/Fed Cup, and related team competitions. |
| `O` | ATP/WTA | `olympics` | Olympic events. |
| `E` | ATP/WTA | `exhibition` | Exhibition events where present. |
| `J` | ATP/WTA | `junior` | Junior events where present. |
| `T` | ATP/WTA | `team_tennis` | Team-tennis events where present. |

## Current Diagnostic Coverage

After the 2026-09-09 refresh, persisted segment rows are distributed as:

| Event level | Segment rows |
|---|---:|
| `itf_level` | 396 |
| `challenger_level` | 232 |
| `grand_slam` | 232 |
| `tour_level` | 228 |
| `team_cup` | 76 |

Current mapping report: `outputs/tables/match_event_level_mapping.csv`.

Current hard gate: `uv run tennis-sabermetrics evaluate-match-diagnostics --fail-on-unmapped-events`.

Current unmapped source rows: 0.

dbt also includes two source-event validation tests:

- `gold_match_features_event_codes_mapped` fails when `tennis.gold_match_features_asof` contains a tournament-level code that maps to `unknown`.
- `gold_event_level_mapping_no_unmapped_rows` fails when the persisted diagnostic report contains unmapped rows.

High-performing missing-rank findings should still be described as diagnostics rather than model claims. The largest missing-rank segments remain fallback-archive sourced and are concentrated in ITF/challenger populations.
