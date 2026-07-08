# Dataset Registry — Tennis Sabermetrics

_Last updated: 2026-07-08_

## Purpose

This registry tracks all datasets acquired or targeted for the Tennis Empirical Analysis project under Savepoint Analytics.

Use it to:

- Know what data has already been acquired.
- Track data freshness and source commit/version.
- Record storage locations in MinIO, PostgreSQL, and Git.
- Track license obligations and commercial-use constraints.
- Prevent accidental redistribution of restricted third-party data.

---

## Storage Conventions

| Layer | Storage | Purpose |
|---|---|---|
| Raw | MinIO `tennis-sabermetrics/raw/...` | Immutable source snapshots, original CSV/HTML/files, commit hashes, checksums. |
| Bronze | MinIO `tennis-sabermetrics/bronze/...` | Source-shaped Parquet conversions with metadata columns. |
| Silver | PostgreSQL schema `tennis` + Parquet | Normalized entities: players, matches, rankings, points, shots. |
| Gold | PostgreSQL marts + Parquet | Feature tables, model inputs, public analysis tables. |
| Git | Repo only | Code, docs, dbt models, manifests, schemas, tiny test fixtures. No bulk raw data. |

---

## Dataset Registry

### Canonical Tennis Abstract / Jeff Sackmann Sources

| Dataset | Source | Format | Intended Location | Last Updated Locally | Update Freq | Status | License | Commercial Use | Notes |
|---|---|---|---|---|---|---|---|---|---|
| ATP results/rankings/stats | `https://github.com/JeffSackmann/tennis_atp` | CSV | MinIO raw + PostgreSQL `tennis` | — | Regular, not guaranteed | Pending | CC BY-NC-SA 4.0 | No, unless permission | Canonical ATP match/ranking source. Prefer over forks. |
| WTA results/rankings/stats | `https://github.com/JeffSackmann/tennis_wta` | CSV | MinIO raw + PostgreSQL `tennis` | — | Regular, not guaranteed | Pending | CC BY-NC-SA 4.0 | No, unless permission | Canonical WTA match/ranking source. |
| Match Charting Project | `https://github.com/JeffSackmann/tennis_MatchChartingProject` | CSV | MinIO raw + PostgreSQL point/shot tables | — | Periodic | Pending | CC BY-NC-SA 4.0 | No, unless permission | Richest public tactical/shot dataset; charting coverage is selected, not random. |
| Grand Slam point-by-point | `https://github.com/JeffSackmann/tennis_slam_pointbypoint` | CSV | MinIO raw + PostgreSQL point tables | — | After slams, not guaranteed | Pending | CC BY-NC-SA 4.0 | No, unless permission | Prefer canonical over `halepmania` fork. Columns vary by event/year. |
| Sequential point-by-point | `https://github.com/JeffSackmann/tennis_pointbypoint` | CSV | MinIO raw + PostgreSQL point-sequence tables | — | Historical/static-ish | Pending | CC BY-NC-SA 4.0 | No, unless permission | Encoded point sequences; messy and incomplete. |
| Tennis misc algorithms | `https://github.com/JeffSackmann/tennis_misc` | Python scripts | Git reference only; do not vendor | — | Static | Reference | CC BY-NC-SA 4.0 | No, unless permission | Probability algorithms; rewrite independently if needed. |
| Tennis visualization examples | `https://github.com/JeffSackmann/tennis_viz` | Python/Altair/data snippets | Git reference only; do not vendor unless license clarified | — | Static | Reference | Unclear for code; underlying data often CC BY-NC-SA | Treat as no commercial use | Use for ideas, not copied code. |
| Tennis Abstract Elo pages | `https://tennisabstract.com/reports/atp_elo_ratings.html`, `https://tennisabstract.com/reports/wta_elo_ratings.html` | HTML tables | MinIO raw HTML + PostgreSQL `elo_ratings_reference` | — | Weekly-ish | Pending | Treat as Tennis Abstract terms / attribution required | No commercial use unless permission | Benchmark/reference, not primary model source. |

### User-Listed Forks / Alternate URLs

| Dataset / repo | User-listed source | Preferred handling | Status | License / risk notes |
|---|---|---|---|---|
| ATP data fork | `https://github.com/oz-tmg/tennis_atp` | Prefer canonical `JeffSackmann/tennis_atp` | Reference only | Forked data lineage; use only if canonical unavailable or fork contains verified unique content. |
| WTA data fork | `https://github.com/ppaulojr/tennis_wta` | Prefer canonical `JeffSackmann/tennis_wta` | Reference only | Fork has no clearly surfaced license in GitHub page; treat as derived from canonical CC BY-NC-SA. |
| Grand Slam PBP old fork | `github.com/halepmania/tennis_slam_pointbypoint` | Prefer canonical `JeffSackmann/tennis_slam_pointbypoint` | Reference only | Appears older/stale. Use canonical for license clarity and current data. |
| Point-by-point fork | `https://github.com/ppaulojr/tennis_pointbypoint` | Prefer canonical `JeffSackmann/tennis_pointbypoint` | Reference only | Treat as derived non-commercial data. |
| Tennis viz fork | `https://github.com/satya469/tennis_viz` | Prefer canonical `JeffSackmann/tennis_viz` | Reference only | No license found in fork page; do not copy code. |
| Tennis misc fork | `https://github.com/halepmania/tennis_misc` | Prefer canonical `JeffSackmann/tennis_misc` | Reference only | No license surfaced in fork page; canonical has CC BY-NC-SA. |

### Additional Public or Semi-Public Sources

| Dataset | Source | Format | Intended Location | Last Updated Locally | Update Freq | Status | License | Commercial Use | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Tennis-Data.co.uk results/odds | `https://www.tennis-data.co.uk/` | CSV/XLS | Isolated MinIO `raw_unverified_terms/` only | — | Current + historical | Optional | Terms unclear | Do not use commercially until verified | Useful for odds benchmarks. Do not redistribute. |
| Kaggle Tennis Match Charting mirror | Kaggle mirror of MCP | CSV | Avoid unless needed | — | Varies | Not preferred | CC BY-NC-SA 4.0 mirror | No | Prefer original GitHub source. |
| Kaggle ATP/WTA mirrors | Kaggle datasets derived from Sackmann or Tennis-Data | CSV | Avoid unless needed | — | Varies | Not preferred | Varies; often derivative | Usually no | Prefer original source to avoid license ambiguity. |
| TML-Database | `https://github.com/Tennismylife/TML-Database` | CSV/DB | Isolated private evaluation only | — | Live updated | Optional | Non-commercial unless permitted | No, unless permission | May fill recent ATP gaps; verify lineage and terms. |
| ATP World Tour scrape scripts | `https://github.com/serve-and-volley/atp-world-tour-tennis-data` | Python/R/SQL/CSV | Reference only | — | Static as of 2023 | Reference | CC BY 4.0 for repo | Maybe, but website ToS must be checked | Scrapers may break and official site terms matter. |
| Stats Perform WTA official feed | `https://www.statsperform.com/wta/` | Licensed feed/API | Not stored until licensed | — | Live | Not acquired | Commercial contract | Yes if licensed | Potential paid data source, not public. |

### Methodology / Code References

| Repo | Source | Language | Status | Code license | Data license concern | Notes |
|---|---|---|---|---|---|---|
| Ultimate Tennis Statistics / Tennis Crystal Ball | `https://github.com/mcekovic/tennis-crystal-ball` | Java | Reference | Apache-2.0 for code | Algorithms CC BY-NC-SA 4.0 | Useful for Elo variants and feature ideas. |
| tennis-xgboost-autoresearch | `https://github.com/buildoak/tennis-xgboost-autoresearch` | Python | Reference | MIT for code | Data CC BY-NC-SA 4.0 | Excellent reference for evaluation guardrails and Goodhart risks. |
| tennis_match_prediction | `https://github.com/jgollub1/tennis_match_prediction` | Python | Reference | MIT | Uses Sackmann data | Useful for pre-match/in-match prediction structure. |
| tennis_preds | `https://github.com/mxa256/tennis_preds` | R | Reference | CC0-1.0 displayed by GitHub | Uses Sackmann data | Useful for leakage-aware pipeline design; R-centric. |
| tennis-elo | `https://github.com/hongsuh7/tennis-elo` | Python/Jupyter | Reference | No license surfaced | Uses Sackmann data | Use ideas only; do not copy code unless license clarified. |
| 04-Tennis-Point-by-Point-Project | `https://github.com/haroldmli/04-Tennis-Point-by-Point-Project` | Mixed | Reference | License unclear | Uses Sackmann data and live score scraping | Methodology reference only. |

---

## Required Metadata Table

Create this table before ingesting data:

```sql
create schema if not exists tennis;

create table if not exists tennis.source_license (
    source_key text primary key,
    source_name text not null,
    source_url text not null,
    license_name text,
    license_url text,
    attribution_required boolean not null default true,
    non_commercial_only boolean not null default true,
    share_alike_required boolean not null default false,
    redistribution_allowed boolean,
    commercial_use_allowed boolean,
    notes text,
    verified_at timestamptz not null default now()
);

create table if not exists tennis.raw_manifest (
    manifest_id bigserial primary key,
    source_key text not null references tennis.source_license(source_key),
    snapshot_date date not null,
    source_commit_sha text,
    source_file_path text not null,
    minio_uri text not null,
    file_sha256 text not null,
    row_count bigint,
    acquired_at timestamptz not null default now(),
    acquired_by text not null default current_user,
    notes text,
    unique (source_key, snapshot_date, source_file_path, file_sha256)
);
```

---

## Acquisition Priority

### Immediate

1. `JeffSackmann/tennis_atp`
2. `JeffSackmann/tennis_wta`
3. Tennis Abstract ATP/WTA Elo pages as benchmark snapshots
4. `JeffSackmann/tennis_MatchChartingProject`

### Next

5. `JeffSackmann/tennis_slam_pointbypoint`
6. `JeffSackmann/tennis_pointbypoint`
7. `JeffSackmann/tennis_misc` as algorithm reference only
8. `JeffSackmann/tennis_viz` as visualization reference only

### Optional / Isolated

9. Tennis-Data.co.uk for betting odds benchmark after terms review
10. TML-Database for recent ATP coverage after license review
11. Official/commercial feeds only if pursuing paid product validation

---

## Notes on Attribution

For any output using Tennis Abstract / Jeff Sackmann data, include attribution similar to:

> Data derived from Jeff Sackmann / Tennis Abstract repositories. Original data and algorithms are licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International unless otherwise stated. This project is non-commercial research/portfolio work and does not redistribute raw third-party data.

---

## Update Log

| Date | Update |
|---|---|
| 2026-06-28 | Initial tennis dataset registry created, including user-provided repos, canonical alternatives, licensing notes, and storage conventions. |
| 2026-06-29 | Added source license seed files and PostgreSQL bootstrap SQL as the first metadata guardrail before source ingestion. |
| 2026-07-08 | Added source-sync primitives for canonical Git sources and bronze metadata conversion helpers; no raw data committed. |
