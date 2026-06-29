"""Prefect wrapper placeholder for source ingestion."""

from __future__ import annotations

from tennis_sabermetrics.ingest.git_sources import plan_source_sync


def build_dry_run_plan() -> int:
    return len(plan_source_sync(("jeffsackmann_tennis_atp",), dry_run=True))

