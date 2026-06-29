# Public Data Sources Reference — Tennis Sabermetrics

_Last updated: 2026-06-29_

## Purpose

Master reference for public and semi-public tennis data sources used or considered for the Tennis Empirical Analysis project.

This document includes:

- Source descriptions.
- Access patterns.
- Python/R usage notes.
- Licensing and attribution requirements.
- Data quality notes.
- Recommendations for what to use, avoid, or treat as reference-only.

---

## Source Selection Principles

1. Prefer original/canonical sources over mirrors and forks.
2. Preserve raw snapshots with source URL, commit SHA, download date, and license.
3. Do not redistribute third-party raw data unless explicitly allowed.
4. Treat non-commercial data as portfolio/research-only.
5. Isolate sources with unclear terms from public outputs and commercial workflows.
6. Build Savepoint-owned code independently; do not copy unlicensed GitHub code.

---

## Core Canonical Sources

### Jeff Sackmann / Tennis Abstract — ATP Results, Rankings, Stats

**URL:** `https://github.com/JeffSackmann/tennis_atp`  
**Format:** CSV files by season plus player/ranking files.  
**Use for:** ATP match outcome data, rankings, player biographical fields, match stats, doubles, challengers/futures where available.  
**License:** CC BY-NC-SA 4.0. Attribution required. Non-commercial use only. Share-alike obligations may apply.  
**Commercial use:** Not without separate permission.

Acquisition:

```bash
git clone https://github.com/JeffSackmann/tennis_atp external/tennis_atp
cd external/tennis_atp
git rev-parse HEAD
```

Python access pattern:

```python
from pathlib import Path
import pandas as pd

root = Path("external/tennis_atp")
matches_2025 = pd.read_csv(root / "atp_matches_2025.csv")
players = pd.read_csv(root / "atp_players.csv")
rankings = pd.read_csv(root / "atp_rankings_current.csv", header=None)
```

Notes:

- MatchStats are integer totals, not percentages. Compute percentages carefully.
- Stats are more complete in the modern era than early historical periods.
- Rankings and ages are as of tournament date.
- Some matches have missing stats due to source gaps or sanity-check removals.

---

### Jeff Sackmann / Tennis Abstract — WTA Results, Rankings, Stats

**URL:** `https://github.com/JeffSackmann/tennis_wta`  
**Format:** CSV files by season plus player/ranking files.  
**Use for:** WTA match outcome data, rankings, player biographical fields, ITF/qualifying files.  
**License:** CC BY-NC-SA 4.0.  
**Commercial use:** Not without separate permission.

Acquisition:

```bash
git clone https://github.com/JeffSackmann/tennis_wta external/tennis_wta
cd external/tennis_wta
git rev-parse HEAD
```

Python access pattern:

```python
from pathlib import Path
import pandas as pd

root = Path("external/tennis_wta")
matches_2025 = pd.read_csv(root / "wta_matches_2025.csv")
players = pd.read_csv(root / "wta_players.csv")
rankings = pd.read_csv(root / "wta_rankings_current.csv", header=None)
```

Notes:

- WTA fields are broadly parallel to ATP but not always identical.
- Always standardize tour/gender/source fields explicitly.
- Do not assume all ranking files have equal historical completeness.

---

### Tennis Abstract Match Charting Project

**URL:** `https://github.com/JeffSackmann/tennis_MatchChartingProject`  
**Format:** CSV. Match metadata, point files, stats files, shot-by-shot charting columns.  
**Use for:** Tactical analysis, shot patterns, point-level states, return depth, serve direction, errors, winners, rally patterns.  
**License:** CC BY-NC-SA 4.0.  
**Commercial use:** Not without separate permission.

Acquisition:

```bash
git clone https://github.com/JeffSackmann/tennis_MatchChartingProject external/tennis_MatchChartingProject
cd external/tennis_MatchChartingProject
git rev-parse HEAD
```

Python access pattern:

```python
from pathlib import Path
import pandas as pd

root = Path("external/tennis_MatchChartingProject")
men_matches = pd.read_csv(root / "charting-m-matches.csv")
women_matches = pd.read_csv(root / "charting-w-matches.csv")
```

Notes:

- This is the best public source for tactical/shot-level tennis.
- Charted matches are contributor-selected, not representative of all matches.
- Learn the charting notation before building production transformations.
- The raw point files may be large and may require chunked reads.

---

### Grand Slam Point-by-Point

**Canonical URL:** `https://github.com/JeffSackmann/tennis_slam_pointbypoint`  
**User-listed older fork:** `https://github.com/halepmania/tennis_slam_pointbypoint`  
**Format:** CSV, event-level `-matches.csv` and `-points.csv`.  
**Use for:** Grand Slam point-level modeling, serve speed/rally length where available, slam-specific tactical patterns.  
**License:** CC BY-NC-SA 4.0 in canonical repo.  
**Commercial use:** Not without separate permission.

Acquisition:

```bash
git clone https://github.com/JeffSackmann/tennis_slam_pointbypoint external/tennis_slam_pointbypoint
cd external/tennis_slam_pointbypoint
git rev-parse HEAD
```

Notes:

- Columns vary by tournament and year.
- Some events lack first/second serve indicators, rally length, serve speed, or winner type.
- Since 2023, Australian Open and French Open extraction may be incomplete or not attempted in the canonical source.
- Use tournament/year-specific validation.

---

### Sequential Point-by-Point

**Canonical URL:** `https://github.com/JeffSackmann/tennis_pointbypoint`  
**User-listed fork:** `https://github.com/ppaulojr/tennis_pointbypoint`  
**Format:** CSV with compact point strings.  
**Use for:** Point sequence parsing, game/set/match win probability, Markov-style models, serve/return point outcomes.  
**License:** CC BY-NC-SA 4.0 in canonical repo.  
**Commercial use:** Not without separate permission.

Point string notation:

- `S` = server won point.
- `R` = returner won point.
- `A` = ace.
- `D` = double fault.
- `.` separates sets.
- `;` separates games.
- `/` indicates serve changes during tiebreaks.

Notes:

- Dataset is extensive but messy.
- Retirements are excluded because scores are not valid for full parsing.
- Duplicates and mis-parsed matches may exist.
- Lower-level coverage is less complete than tour-level coverage.

---

### Tennis Abstract Elo Ratings

**ATP:** `https://tennisabstract.com/reports/atp_elo_ratings.html`  
**WTA:** `https://tennisabstract.com/reports/wta_elo_ratings.html`  
**Format:** HTML tables.  
**Use for:** Benchmark/reference Elo ratings, surface Elo comparisons, article context.  
**License/terms:** Treat as Tennis Abstract attribution-required, non-commercial unless permission is obtained.  
**Commercial use:** Not without permission.

Python access pattern:

```python
import pandas as pd

atp_elo = pd.read_html("https://tennisabstract.com/reports/atp_elo_ratings.html")[0]
wta_elo = pd.read_html("https://tennisabstract.com/reports/wta_elo_ratings.html")[0]
```

Notes:

- Pages are updated weekly-ish.
- Use as a reference benchmark. Build your own reproducible Elo model for project outputs.
- Surface-specific Elo columns are useful for validating your own implementation.

---

## User-Listed Forks and How to Treat Them

| User-listed repo | Recommended action | Reason |
|---|---|---|
| `https://github.com/JeffSackmann/tennis_MatchChartingProject` | Use directly | Canonical source. |
| `github.com/halepmania/tennis_slam_pointbypoint` | Prefer `JeffSackmann/tennis_slam_pointbypoint` | User-listed fork appears older; canonical repo has current license text. |
| `https://github.com/oz-tmg/tennis_atp` | Prefer `JeffSackmann/tennis_atp` | Fork lineage and freshness uncertain. |
| `https://github.com/ppaulojr/tennis_wta` | Prefer `JeffSackmann/tennis_wta` | Fork page did not clearly surface license. |
| `https://github.com/satya469/tennis_viz` | Prefer `JeffSackmann/tennis_viz`; reference only | No license surfaced; do not copy code. |
| `https://github.com/ppaulojr/tennis_pointbypoint` | Prefer `JeffSackmann/tennis_pointbypoint` | Use canonical for license clarity. |
| `https://github.com/halepmania/tennis_misc` | Prefer `JeffSackmann/tennis_misc` | Canonical repo has license text. |

---

## Additional Sources Worth Considering

### Tennis-Data.co.uk

**URL:** `https://www.tennis-data.co.uk/`  
**Format:** CSV/XLS.  
**Use for:** Historical match results and betting odds.  
**Best use:** Benchmark forecasts against closing/opening odds if terms allow.  
**License/terms:** Unclear from source snippets; verify before using beyond private experiments.  
**Commercial use:** Do not use commercially until terms are explicitly verified.

Recommendation:

- Store in isolated path `raw_unverified_terms/tennis_data_co_uk/`.
- Do not publish derived odds tables until terms are reviewed.
- Do not mix into public marts by default.

---

### TML-Database

**URL:** `https://github.com/Tennismylife/TML-Database`  
**Format:** Repository data.  
**Use for:** Potential recent ATP match coverage.  
**License/terms:** Non-commercial unless explicitly permitted.  
**Commercial use:** No, unless permission.

Recommendation:

- Treat as optional and isolated.
- Use only if it fills a clear gap in recent ATP coverage.
- Track lineage carefully because it is inspired by / based on Jeff Sackmann data.

---

### Ultimate Tennis Statistics / Tennis Crystal Ball

**URL:** `https://github.com/mcekovic/tennis-crystal-ball`  
**Format:** Java application and algorithms.  
**Use for:** Methodology reference: Elo variants, GOAT-style scoring, match prediction, tournament forecasts, UI ideas.  
**License:** Code Apache-2.0; algorithms including custom Elo/match prediction/tournament forecast are CC BY-NC-SA 4.0.  
**Commercial use:** Code may be usable under Apache-2.0, but algorithm license constraints must be respected.

Recommendation:

- Do not port algorithms line-by-line.
- Use as literature/reference for what features exist in a mature tennis analytics system.
- Build independent Python implementations.

---

### tennis-xgboost-autoresearch

**URL:** `https://github.com/buildoak/tennis-xgboost-autoresearch`  
**Format:** Python package and research loop.  
**Use for:** XGBoost pipeline ideas, feature engineering taxonomy, temporal evaluation, Goodhart-proofing.  
**License:** Code MIT; bundled data CC BY-NC-SA 4.0.  
**Commercial use:** Code potentially yes under MIT; data no without permission.

Recommendation:

- Study its immutable evaluation/gate design.
- Copy no data.
- If adapting code patterns, preserve attribution and verify license compatibility.

---

### jgollub1 tennis_match_prediction

**URL:** `https://github.com/jgollub1/tennis_match_prediction`  
**Format:** Python notebooks/scripts.  
**Use for:** Pre-match and in-match prediction methodology.  
**License:** MIT.  
**Data:** Uses Jeff Sackmann datasets, so data-derived artifacts remain non-commercial.

Recommendation:

- Useful for seeing how pre-match and in-match prediction were framed.
- Rebuild with project-specific tests and strict feature lineage.

---

### mxa256 tennis_preds

**URL:** `https://github.com/mxa256/tennis_preds`  
**Format:** R package/project.  
**Use for:** Leakage-aware modeling approach, feature pipeline structure, CLAUDE-style documentation inspiration.  
**License:** GitHub displays CC0-1.0 for repo code.  
**Data:** Trained on Jeff Sackmann data, so data outputs are constrained.

Recommendation:

- Use as a conceptual reference.
- Keep project Python-centric and port only ideas, not direct code unless verified.

---

### serve-and-volley ATP World Tour Tennis Data

**URL:** `https://github.com/serve-and-volley/atp-world-tour-tennis-data`  
**Format:** Python, R, SQL, CSV.  
**Use for:** Scraping approach and historical ATP site extraction.  
**License:** CC BY 4.0 for repo according to README.  
**Caution:** Official ATP site terms and layout changes matter.

Recommendation:

- Reference only unless terms review supports scraping.
- Do not rely on brittle scrapers as the first ingestion path.

---

### Stats Perform WTA Official Feed

**URL:** `https://www.statsperform.com/wta/`  
**Format:** Commercial licensed feed/API.  
**Use for:** Future commercial-grade WTA data source.  
**Public:** No.  
**Commercial use:** Yes only under contract.

Recommendation:

- Track as a future commercial pathway.
- Not needed for initial public portfolio.

---

## Data Quality Checklist

Before building analytics on a source, answer:

- What exact source URL and commit/date was used?
- What license applies?
- Can raw data be redistributed?
- Is commercial use allowed?
- What years/tours/surfaces are covered?
- Are rankings and stats available as-of the match date?
- Are retirements/walkovers included or excluded?
- Are player IDs stable?
- Are columns consistent across years?
- Is the sample representative or selected?
- What known missingness exists?

---

## Source Manifest Fields

Every raw snapshot should record:

```yaml
source_key: jeffsackmann_tennis_atp
source_name: Jeff Sackmann Tennis ATP
source_url: https://github.com/JeffSackmann/tennis_atp
source_commit_sha: <git sha>
snapshot_date: YYYY-MM-DD
acquired_at: YYYY-MM-DDTHH:MM:SSZ
license_name: CC BY-NC-SA 4.0
license_url: https://creativecommons.org/licenses/by-nc-sa/4.0/
commercial_use_allowed: false
redistribution_allowed: false
raw_storage_uri: s3://tennis-sabermetrics/raw/...
file_count: 0
checksum_manifest: checksums.sha256
notes: "Raw third-party data; do not commit to Git or redistribute."
```

---

## Attribution Template

Use in notebooks, dashboards, README files, and public posts:

> Data derived from Jeff Sackmann / Tennis Abstract repositories and/or The Tennis Abstract Match Charting Project. Original sources are licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International unless otherwise stated. This project is non-commercial research/portfolio work and does not redistribute raw third-party data.

---

## Recommended First Acquisition Script Behavior

`sync_sources.py` should:

1. Clone or fetch canonical repositories.
2. Record commit SHA.
3. Generate SHA256 checksums for every source file.
4. Copy raw files to MinIO under source/snapshot/commit path.
5. Write a manifest row for each file.
6. Convert CSVs to bronze Parquet.
7. Refuse to sync sources whose license metadata is missing unless `--allow-unverified-source` is passed.

---

## Update Log

| Date | Update |
|---|---|
| 2026-06-28 | Initial public data source reference created for tennis project. |
| 2026-06-29 | Added initial dry-run source acquisition behavior and license metadata seeds to the repository scaffold. |
