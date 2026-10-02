"""Command-line entry points for the project."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from tennis_sabermetrics.config import (
    CANONICAL_GIT_SOURCES,
    FALLBACK_ARCHIVE_SOURCE_KEY,
    GIT_SOURCES,
)
from tennis_sabermetrics.evaluation.article_charts import export_match_article_charts
from tennis_sabermetrics.evaluation.diagnostics import (
    DEFAULT_DIAGNOSTIC_FEATURE_CACHE_PATH,
    evaluate_match_diagnostics_postgres,
)
from tennis_sabermetrics.evaluation.walk_forward import (
    DEFAULT_WALK_FORWARD_FEATURE_CACHE_PATH,
    evaluate_walk_forward_postgres,
)
from tennis_sabermetrics.features.match_features import build_gold_match_features_postgres
from tennis_sabermetrics.ingest.bronze import build_bronze_for_source
from tennis_sabermetrics.ingest.git_sources import plan_source_sync, sync_git_source
from tennis_sabermetrics.ingest.postgres import execute_sql_file
from tennis_sabermetrics.ingest.warehouse import (
    enrich_raw_manifest_row_counts,
    load_bronze_postgres,
)
from tennis_sabermetrics.models.match_outcome import (
    DEFAULT_BASELINE_FEATURE_CACHE_PATH,
    evaluate_match_baselines_postgres,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tennis-sabermetrics",
        description="Tennis sabermetrics data and modeling utilities.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync = subparsers.add_parser("sync-sources", help="Plan or run source acquisition.")
    sync.add_argument("--source", choices=sorted(GIT_SOURCES), action="append")
    sync.add_argument("--dry-run", action="store_true", help="Print acquisition plan only.")
    sync.add_argument(
        "--snapshot-date",
        type=date.fromisoformat,
        help="Snapshot date in YYYY-MM-DD format. Defaults to today.",
    )
    sync.add_argument(
        "--external-repos-root",
        type=Path,
        help="Override EXTERNAL_REPOS_ROOT for cloned/fetched source repositories.",
    )
    sync.add_argument(
        "--copy-raw-to-minio",
        action="store_true",
        help="Copy fetched raw source files to the configured MinIO bucket.",
    )
    sync.add_argument(
        "--write-raw-manifest",
        action="store_true",
        help="Persist raw manifest rows to PostgreSQL after copying raw files.",
    )
    sync.add_argument(
        "--allow-unverified-source",
        action="store_true",
        help="Allow sources without complete license metadata.",
    )
    sync.add_argument(
        "--source-subdir",
        choices=("atp", "wta", "slam_pointbypoint"),
        help="Sync only a reviewed archive subdirectory. Intended for fallback archive sources.",
    )

    bronze = subparsers.add_parser("build-bronze", help="Convert source CSVs to bronze Parquet.")
    bronze.add_argument(
        "--source",
        required=True,
        choices=("jeffsackmann_tennis_atp", "jeffsackmann_tennis_wta", FALLBACK_ARCHIVE_SOURCE_KEY),
    )
    bronze.add_argument(
        "--archive-tour",
        choices=("atp", "wta"),
        help="Tour subdirectory to convert when --source is the fallback archive.",
    )
    bronze.add_argument(
        "--snapshot-date",
        required=True,
        type=date.fromisoformat,
        help="Snapshot date in YYYY-MM-DD format.",
    )
    bronze.add_argument("--source-root", type=Path, help="Override synced source repository path.")
    bronze.add_argument("--bronze-root", type=Path, help="Override BRONZE_DATA_ROOT.")
    bronze.add_argument("--source-commit-sha", help="Commit SHA recorded for bronze metadata.")

    load_bronze = subparsers.add_parser(
        "load-bronze-postgres",
        help="Load bronze Parquet outputs into PostgreSQL bronze landing tables.",
    )
    load_bronze.add_argument("--bronze-root", type=Path, default=Path(".local/bronze"))
    load_bronze.add_argument(
        "--snapshot-date",
        required=True,
        type=date.fromisoformat,
        help="Snapshot date in YYYY-MM-DD format.",
    )
    load_bronze.add_argument("--source", default=FALLBACK_ARCHIVE_SOURCE_KEY, choices=sorted(GIT_SOURCES))
    load_bronze.add_argument("--tour", choices=("atp", "wta"), action="append")
    load_bronze.add_argument(
        "--append",
        action="store_true",
        help="Append to existing bronze landing tables instead of truncating first.",
    )

    enrich_manifest = subparsers.add_parser(
        "enrich-raw-manifest-row-counts",
        help="Update raw manifest row_count values from local raw snapshot files.",
    )
    enrich_manifest.add_argument("--source-root", type=Path, default=Path(".local/external/tennis-sackmann-archive"))
    enrich_manifest.add_argument(
        "--snapshot-date",
        required=True,
        type=date.fromisoformat,
        help="Snapshot date in YYYY-MM-DD format.",
    )
    enrich_manifest.add_argument("--source", default=FALLBACK_ARCHIVE_SOURCE_KEY, choices=sorted(GIT_SOURCES))

    bootstrap = subparsers.add_parser("bootstrap-postgres", help="Create metadata tables.")
    bootstrap.add_argument(
        "--sql-file",
        type=Path,
        default=Path("scripts/bootstrap_postgres.sql"),
        help="Bootstrap SQL file.",
    )

    gold_features = subparsers.add_parser(
        "build-gold-match-features",
        help="Build leakage-safe pre-match feature table in PostgreSQL.",
    )
    gold_features.add_argument(
        "--snapshot-date",
        required=True,
        type=date.fromisoformat,
        help="Snapshot date in YYYY-MM-DD format.",
    )
    gold_features.add_argument(
        "--start-date",
        type=date.fromisoformat,
        help="Optional first match date to include.",
    )
    gold_features.add_argument(
        "--end-date",
        type=date.fromisoformat,
        help="Optional last match date to include.",
    )
    gold_features.add_argument(
        "--append",
        action="store_true",
        help="Append to the gold feature table instead of truncating it first.",
    )

    baseline_eval = subparsers.add_parser(
        "evaluate-match-baselines",
        help="Evaluate ranking, Elo, surface Elo, and logistic match baselines.",
    )
    baseline_eval.add_argument("--start-date", type=date.fromisoformat)
    baseline_eval.add_argument("--end-date", type=date.fromisoformat)
    baseline_eval.add_argument("--limit", type=int)
    baseline_eval.add_argument(
        "--output-path",
        type=Path,
        default=Path("outputs/tables/match_baseline_evaluation.csv"),
    )
    baseline_eval.add_argument(
        "--no-persist-postgres",
        action="store_true",
        help="Skip writing evaluation rows to tennis.gold_prediction_backtests.",
    )
    baseline_eval.add_argument(
        "--feature-cache-path",
        type=Path,
        default=DEFAULT_BASELINE_FEATURE_CACHE_PATH,
        help=(
            "Reuse or write a snapshot-aware feature cache for baseline evaluation. "
            "Defaults to outputs/cache/match_baseline_features.parquet."
        ),
    )
    baseline_eval.add_argument(
        "--no-feature-cache",
        action="store_true",
        help="Read baseline features directly from PostgreSQL and skip the local cache.",
    )

    diagnostics = subparsers.add_parser(
        "evaluate-match-diagnostics",
        help="Build calibration, missingness, and segmented backtest diagnostics.",
    )
    diagnostics.add_argument("--start-date", type=date.fromisoformat)
    diagnostics.add_argument("--end-date", type=date.fromisoformat)
    diagnostics.add_argument("--limit", type=int)
    diagnostics.add_argument("--probability-bins", type=int, default=10)
    diagnostics.add_argument("--min-segment-size", type=int, default=100)
    diagnostics.add_argument("--output-dir", type=Path, default=Path("outputs/tables"))
    diagnostics.add_argument(
        "--calibration-plot-path",
        type=Path,
        default=Path("outputs/charts/match_prediction_calibration.html"),
    )
    diagnostics.add_argument(
        "--no-persist-postgres",
        action="store_true",
        help="Skip writing diagnostic rows to PostgreSQL gold diagnostic tables.",
    )
    diagnostics.add_argument(
        "--fail-on-unmapped-events",
        action="store_true",
        help="Exit with an error if the event-level mapping report has unmapped tournament codes.",
    )
    diagnostics.add_argument(
        "--feature-cache-path",
        type=Path,
        default=DEFAULT_DIAGNOSTIC_FEATURE_CACHE_PATH,
        help=(
            "Reuse or write a snapshot-aware narrow feature cache for diagnostics. "
            "Defaults to outputs/cache/match_diagnostic_features.parquet."
        ),
    )
    diagnostics.add_argument(
        "--no-feature-cache",
        action="store_true",
        help="Read diagnostics features directly from PostgreSQL and skip the local cache.",
    )

    walk_forward = subparsers.add_parser(
        "evaluate-match-walk-forward",
        help="Evaluate baseline match models across expanding walk-forward windows.",
    )
    walk_forward.add_argument("--first-test-year", type=int, default=2016)
    walk_forward.add_argument("--last-test-year", type=int, default=2025)
    walk_forward.add_argument("--validation-years", type=int, default=3)
    walk_forward.add_argument("--limit", type=int)
    walk_forward.add_argument(
        "--output-path",
        type=Path,
        default=Path("outputs/tables/match_walk_forward_evaluation.csv"),
    )
    walk_forward.add_argument(
        "--no-persist-postgres",
        action="store_true",
        help="Skip writing walk-forward rows to PostgreSQL.",
    )
    walk_forward.add_argument(
        "--feature-cache-path",
        type=Path,
        default=DEFAULT_WALK_FORWARD_FEATURE_CACHE_PATH,
        help=(
            "Reuse or write a snapshot-aware narrow feature cache for walk-forward evaluation. "
            "Defaults to outputs/cache/match_walk_forward_features.parquet."
        ),
    )
    walk_forward.add_argument(
        "--no-feature-cache",
        action="store_true",
        help="Read walk-forward features directly from PostgreSQL and skip the local cache.",
    )

    article_charts = subparsers.add_parser(
        "export-match-article-charts",
        help="Export static SVG charts and captions for the match prediction article.",
    )
    article_charts.add_argument("--table-dir", type=Path, default=Path("outputs/tables"))
    article_charts.add_argument("--output-dir", type=Path, default=Path("outputs/charts/article"))

    subparsers.add_parser("list-sources", help="List configured Git sources.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list-sources":
        for source in GIT_SOURCES.values():
            print(f"{source.source_key}\t{source.source_url}\t{source.license_name}")
        return 0

    try:
        return run_command(args)
    except (FileNotFoundError, ValueError) as exc:
        parser.exit(1, f"error: {exc}\n")

    parser.error(f"Unknown command: {args.command}")
    return 2


def run_command(args: argparse.Namespace) -> int:
    if args.command == "sync-sources":
        if args.source_subdir and (not args.source or len(args.source) != 1):
            raise ValueError("--source-subdir requires exactly one --source")
        source_keys = tuple(args.source) if args.source else tuple(CANONICAL_GIT_SOURCES)
        if args.dry_run:
            plan = plan_source_sync(
                source_keys=source_keys,
                dry_run=True,
                allow_unverified_source=args.allow_unverified_source,
            )
            for item in plan:
                print(
                    f"{item.action}\t{item.source.source_key}\t{item.source.source_url}\t"
                    f"license={item.source.license_name}"
                )
            return 0

        for source_key in source_keys:
            sync_result = sync_git_source(
                source_key,
                external_repos_root=args.external_repos_root,
                snapshot_date=args.snapshot_date,
                allow_unverified_source=args.allow_unverified_source,
                copy_raw_to_minio=args.copy_raw_to_minio,
                write_raw_manifest=args.write_raw_manifest,
                source_subdir=args.source_subdir,
            )
            print(
                f"{sync_result.action}\t{sync_result.source.source_key}\t{sync_result.repo_path}\t"
                f"commit={sync_result.commit_sha}\tchecksums={sync_result.checksum_count}\t"
                f"raw_copies={sync_result.raw_copy_count}\t"
                f"manifest_entries={sync_result.manifest_entry_count}\t"
                f"source_subdir={sync_result.source_subdir or ''}"
            )
        return 0

    if args.command == "build-bronze":
        results = build_bronze_for_source(
            source_key=args.source,
            snapshot_date=args.snapshot_date,
            source_root=args.source_root,
            bronze_root=args.bronze_root,
            source_commit_sha=args.source_commit_sha,
            archive_tour=args.archive_tour,
        )
        for bronze_result in results:
            print(
                f"bronze\t{args.source}\t{bronze_result.table_name}\t"
                f"{bronze_result.source_file_path}\t{bronze_result.parquet_path}\t"
                f"rows={bronze_result.row_count}"
            )
        return 0

    if args.command == "bootstrap-postgres":
        execute_sql_file(str(args.sql_file))
        print(f"bootstrapped-postgres\t{args.sql_file}")
        return 0

    if args.command == "load-bronze-postgres":
        load_results = load_bronze_postgres(
            bronze_root=args.bronze_root,
            snapshot_date=args.snapshot_date,
            source_key=args.source,
            tours=tuple(args.tour) if args.tour else ("atp", "wta"),
            replace=not args.append,
        )
        for load_result in load_results:
            print(
                f"loaded-bronze-postgres\t{load_result.table_name}\t"
                f"rows={load_result.row_count}"
            )
        return 0

    if args.command == "enrich-raw-manifest-row-counts":
        enrichment_result = enrich_raw_manifest_row_counts(
            source_root=args.source_root,
            snapshot_date=args.snapshot_date,
            source_key=args.source,
        )
        print(
            "enriched-raw-manifest-row-counts\t"
            f"updated={enrichment_result.updated_count}\t"
            f"missing={enrichment_result.missing_count}"
        )
        return 0

    if args.command == "build-gold-match-features":
        gold_result = build_gold_match_features_postgres(
            snapshot_date=args.snapshot_date,
            start_date=args.start_date,
            end_date=args.end_date,
            replace=not args.append,
        )
        print(f"built-gold-match-features\t{gold_result.table_name}\trows={gold_result.row_count}")
        return 0

    if args.command == "evaluate-match-baselines":
        baseline_rows = evaluate_match_baselines_postgres(
            output_path=args.output_path,
            persist_postgres=not args.no_persist_postgres,
            start_date=args.start_date,
            end_date=args.end_date,
            limit=args.limit,
            feature_cache_path=None if args.no_feature_cache else args.feature_cache_path,
        )
        for baseline_row in baseline_rows:
            roc_auc = "" if baseline_row.roc_auc is None else f"{baseline_row.roc_auc:.6f}"
            print(
                "match-baseline\t"
                f"{baseline_row.model_name}\t{baseline_row.split}\t"
                f"log_loss={baseline_row.log_loss:.6f}\t"
                f"brier={baseline_row.brier_score:.6f}\t"
                f"roc_auc={roc_auc}\t"
                f"accuracy={baseline_row.accuracy:.6f}\t"
                f"n={baseline_row.sample_size}"
            )
        return 0

    if args.command == "evaluate-match-diagnostics":
        diagnostic_result = evaluate_match_diagnostics_postgres(
            output_dir=args.output_dir,
            calibration_plot_path=args.calibration_plot_path,
            persist_postgres=not args.no_persist_postgres,
            start_date=args.start_date,
            end_date=args.end_date,
            limit=args.limit,
            probability_bins=args.probability_bins,
            min_segment_size=args.min_segment_size,
            feature_cache_path=None if args.no_feature_cache else args.feature_cache_path,
        )
        print(
            "match-diagnostics\t"
            f"calibration_rows={len(diagnostic_result.calibration_rows)}\t"
            f"missingness_rows={len(diagnostic_result.missingness_rows)}\t"
            f"segment_rows={len(diagnostic_result.segment_rows)}\t"
            f"source_composition_rows={len(diagnostic_result.source_composition_rows)}\t"
            f"event_mapping_rows={len(diagnostic_result.event_mapping_rows)}\t"
            f"unmapped_event_rows={diagnostic_result.unmapped_event_rows}\t"
            f"calibration_plot={diagnostic_result.calibration_plot_path or ''}"
        )
        if diagnostic_result.unmapped_event_rows:
            message = (
                "warning: event-level mapping has "
                f"{diagnostic_result.unmapped_event_rows} unmapped source rows; "
                f"see {args.output_dir / 'match_event_level_mapping.csv'}"
            )
            if args.fail_on_unmapped_events:
                raise ValueError(message)
            print(message, file=sys.stderr)
        return 0

    if args.command == "evaluate-match-walk-forward":
        walk_forward_rows = evaluate_walk_forward_postgres(
            output_path=args.output_path,
            persist_postgres=not args.no_persist_postgres,
            first_test_year=args.first_test_year,
            last_test_year=args.last_test_year,
            validation_years=args.validation_years,
            limit=args.limit,
            feature_cache_path=None if args.no_feature_cache else args.feature_cache_path,
        )
        for walk_forward_row in walk_forward_rows:
            roc_auc = (
                "" if walk_forward_row.roc_auc is None else f"{walk_forward_row.roc_auc:.6f}"
            )
            print(
                "match-walk-forward\t"
                f"{walk_forward_row.window_label}\t{walk_forward_row.model_name}\t"
                f"log_loss={walk_forward_row.log_loss:.6f}\t"
                f"brier={walk_forward_row.brier_score:.6f}\t"
                f"roc_auc={roc_auc}\t"
                f"accuracy={walk_forward_row.accuracy:.6f}\t"
                f"n={walk_forward_row.sample_size}"
            )
        return 0

    if args.command == "export-match-article-charts":
        chart_paths = export_match_article_charts(
            table_dir=args.table_dir,
            output_dir=args.output_dir,
        )
        for chart_path in chart_paths:
            print(f"article-chart\t{chart_path}")
        return 0

    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
