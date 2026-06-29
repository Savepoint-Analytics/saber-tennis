"""Checksum and raw manifest utilities."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class RawManifestEntry:
    source_key: str
    snapshot_date: date
    source_file_path: str
    storage_uri: str
    file_sha256: str
    source_commit_sha: str | None = None
    row_count: int | None = None
    acquired_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str | None = None


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_checksum_manifest(root: Path) -> list[tuple[str, str]]:
    """Return sorted `(relative_path, sha256)` pairs for files under `root`."""

    files = sorted(path for path in root.rglob("*") if path.is_file())
    return [(path.relative_to(root).as_posix(), sha256_file(path)) for path in files]
