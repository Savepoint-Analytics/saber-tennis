"""Canonical Git source acquisition planning and execution."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from tennis_sabermetrics.config import CANONICAL_GIT_SOURCES, ProjectPaths, SourceLicense
from tennis_sabermetrics.ingest.manifests import build_checksum_manifest


@dataclass(frozen=True)
class SourceSyncPlanItem:
    source: SourceLicense
    action: str


@dataclass(frozen=True)
class SourceSyncResult:
    source: SourceLicense
    action: str
    repo_path: Path
    snapshot_date: date
    commit_sha: str | None
    checksum_count: int


def plan_source_sync(
    source_keys: tuple[str, ...],
    *,
    dry_run: bool,
    allow_unverified_source: bool = False,
) -> list[SourceSyncPlanItem]:
    """Return an acquisition plan and refuse missing license metadata by default."""

    items: list[SourceSyncPlanItem] = []
    for source_key in source_keys:
        try:
            source = CANONICAL_GIT_SOURCES[source_key]
        except KeyError as exc:
            raise ValueError(f"Unknown canonical source key: {source_key}") from exc

        if not allow_unverified_source and not source.is_verified_for_default_sync:
            raise ValueError(
                f"Source {source_key} lacks verified license metadata; "
                "pass --allow-unverified-source only for isolated/private evaluation."
            )

        action = "plan-clone-or-fetch" if dry_run else "clone-or-fetch"
        items.append(SourceSyncPlanItem(source=source, action=action))

    return items


def repo_dir_name(source: SourceLicense) -> str:
    return source.source_url.rstrip("/").rsplit("/", maxsplit=1)[-1].removesuffix(".git")


def _git(args: list[str], *, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def sync_git_source(
    source_key: str,
    *,
    external_repos_root: Path | None = None,
    snapshot_date: date | None = None,
    allow_unverified_source: bool = False,
) -> SourceSyncResult:
    """Clone or fetch a canonical Git source and compute source-file checksums."""

    plan = plan_source_sync(
        (source_key,),
        dry_run=False,
        allow_unverified_source=allow_unverified_source,
    )
    source = plan[0].source
    paths = ProjectPaths.from_env()
    root = external_repos_root or paths.external_repos_root
    repo_path = root / repo_dir_name(source)
    root.mkdir(parents=True, exist_ok=True)

    if repo_path.exists():
        _git(["fetch", "--prune"], cwd=repo_path)
        action = "fetched"
    else:
        _git(["clone", source.source_url, str(repo_path)])
        action = "cloned"

    commit_sha = _git(["rev-parse", "HEAD"], cwd=repo_path)
    checksums = build_checksum_manifest(repo_path)
    return SourceSyncResult(
        source=source,
        action=action,
        repo_path=repo_path,
        snapshot_date=snapshot_date or date.today(),
        commit_sha=commit_sha,
        checksum_count=len(checksums),
    )
