"""Command-line entry points for the project."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from tennis_sabermetrics.config import CANONICAL_GIT_SOURCES
from tennis_sabermetrics.ingest.git_sources import plan_source_sync


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tennis-sabermetrics",
        description="Tennis sabermetrics data and modeling utilities.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync = subparsers.add_parser("sync-sources", help="Plan or run source acquisition.")
    sync.add_argument("--source", choices=sorted(CANONICAL_GIT_SOURCES), action="append")
    sync.add_argument("--dry-run", action="store_true", help="Print acquisition plan only.")
    sync.add_argument(
        "--allow-unverified-source",
        action="store_true",
        help="Allow sources without complete license metadata.",
    )

    subparsers.add_parser("list-sources", help="List configured canonical sources.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list-sources":
        for source in CANONICAL_GIT_SOURCES.values():
            print(f"{source.source_key}\t{source.source_url}\t{source.license_name}")
        return 0

    if args.command == "sync-sources":
        source_keys = tuple(args.source) if args.source else tuple(CANONICAL_GIT_SOURCES)
        plan = plan_source_sync(
            source_keys=source_keys,
            dry_run=args.dry_run,
            allow_unverified_source=args.allow_unverified_source,
        )
        for item in plan:
            print(
                f"{item.action}\t{item.source.source_key}\t{item.source.source_url}\t"
                f"license={item.source.license_name}"
            )
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

