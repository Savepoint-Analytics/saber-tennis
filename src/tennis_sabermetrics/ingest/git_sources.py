"""Canonical Git source acquisition planning and execution."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from tennis_sabermetrics.config import GIT_SOURCES, ProjectPaths, SourceLicense
from tennis_sabermetrics.ingest.manifests import build_checksum_manifest
from tennis_sabermetrics.ingest.storage import (
    MinioRawSnapshotStore,
    copy_raw_snapshot,
    raw_manifest_entries_from_copies,
)


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
    raw_copy_count: int = 0
    manifest_entry_count: int = 0
    source_subdir: str | None = None


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
            source = GIT_SOURCES[source_key]
        except KeyError as exc:
            raise ValueError(f"Unknown Git source key: {source_key}") from exc

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
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            text=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise ValueError(f"Git command failed: git {' '.join(args)}: {message}") from exc
    return completed.stdout.strip()


def sync_git_source(
    source_key: str,
    *,
    external_repos_root: Path | None = None,
    snapshot_date: date | None = None,
    allow_unverified_source: bool = False,
    copy_raw_to_minio: bool = False,
    write_raw_manifest: bool = False,
    source_subdir: str | None = None,
) -> SourceSyncResult:
    """Clone or fetch a Git source and compute source-file checksums."""

    plan = plan_source_sync(
        (source_key,),
        dry_run=False,
        allow_unverified_source=allow_unverified_source,
    )
    source = plan[0].source
    paths = ProjectPaths.from_env()
    root = external_repos_root or paths.external_repos_root
    repo_path = root / repo_dir_name(source)
    store = MinioRawSnapshotStore.from_env() if copy_raw_to_minio else None
    if write_raw_manifest and store is None:
        raise ValueError("--write-raw-manifest requires --copy-raw-to-minio")
    root.mkdir(parents=True, exist_ok=True)

    if repo_path.exists():
        _git(["fetch", "--prune"], cwd=repo_path)
        action = "fetched"
    else:
        _git(["clone", source.source_url, str(repo_path)])
        action = "cloned"

    commit_sha = _git(["rev-parse", "HEAD"], cwd=repo_path)
    resolved_snapshot_date = snapshot_date or date.today()
    manifest_root = repo_path / source_subdir if source_subdir else repo_path
    if not manifest_root.exists():
        raise FileNotFoundError(f"Source subdirectory does not exist: {manifest_root}")
    checksums = build_checksum_manifest(manifest_root)
    raw_copy_count = 0
    manifest_entry_count = 0
    if store is not None:
        copies = copy_raw_snapshot(
            source_key=source.source_key,
            repo_path=repo_path,
            snapshot_date=resolved_snapshot_date,
            source_commit_sha=commit_sha,
            store=store,
            source_subdir=source_subdir,
        )
        raw_copy_count = len(copies)
        entries = raw_manifest_entries_from_copies(
            source_key=source.source_key,
            snapshot_date=resolved_snapshot_date,
            source_commit_sha=commit_sha,
            copies=copies,
        )
        manifest_entry_count = len(entries)
        if write_raw_manifest:
            from tennis_sabermetrics.ingest.postgres import RawManifestWriter

            RawManifestWriter.from_env().insert_entries(entries)

    return SourceSyncResult(
        source=source,
        action=action,
        repo_path=repo_path,
        snapshot_date=resolved_snapshot_date,
        commit_sha=commit_sha,
        checksum_count=len(checksums),
        raw_copy_count=raw_copy_count,
        manifest_entry_count=manifest_entry_count,
        source_subdir=source_subdir,
    )
