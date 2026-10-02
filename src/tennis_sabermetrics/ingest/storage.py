"""Raw snapshot storage adapters."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Protocol
from urllib.parse import urlparse

from tennis_sabermetrics.config import MinioSettings
from tennis_sabermetrics.ingest.manifests import RawManifestEntry, build_checksum_manifest


@dataclass(frozen=True)
class RawSnapshotCopy:
    source_file_path: str
    storage_uri: str
    file_sha256: str


class RawSnapshotStore(Protocol):
    def put_file(self, source_path: Path, object_key: str) -> str:
        """Copy `source_path` to `object_key` and return the storage URI."""


@dataclass(frozen=True)
class LocalRawSnapshotStore:
    """Filesystem-backed raw store for tests and local dry runs."""

    root: Path

    def put_file(self, source_path: Path, object_key: str) -> str:
        destination = self.root / object_key
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        return destination.resolve().as_uri()


@dataclass(frozen=True)
class MinioRawSnapshotStore:
    """MinIO-compatible S3 store backed by PyArrow's S3 filesystem."""

    settings: MinioSettings

    @classmethod
    def from_env(cls) -> MinioRawSnapshotStore:
        settings = MinioSettings.from_env()
        settings.validate_for_write()
        return cls(settings=settings)

    def put_file(self, source_path: Path, object_key: str) -> str:
        from pyarrow import fs

        parsed = urlparse(self.settings.endpoint)
        scheme = parsed.scheme or "http"
        endpoint_override = parsed.netloc or parsed.path
        filesystem = fs.S3FileSystem(
            access_key=self.settings.access_key,
            secret_key=self.settings.secret_key,
            scheme=scheme,
            endpoint_override=endpoint_override,
        )
        prefixed_key = str(PurePosixPath(self.settings.prefix or "") / object_key)
        destination = f"{self.settings.bucket}/{prefixed_key}"
        with source_path.open("rb") as input_file:
            with filesystem.open_output_stream(destination) as output_file:
                shutil.copyfileobj(input_file, output_file)
        return f"s3://{self.settings.bucket}/{prefixed_key}"


def raw_snapshot_object_key(
    *,
    source_key: str,
    snapshot_date: date,
    source_commit_sha: str | None,
    relative_path: str,
) -> str:
    commit = source_commit_sha or "unknown"
    return str(
        PurePosixPath("raw")
        / source_key
        / f"snapshot_date={snapshot_date.isoformat()}"
        / f"commit={commit}"
        / relative_path
    )


def copy_raw_snapshot(
    *,
    source_key: str,
    repo_path: Path,
    snapshot_date: date,
    source_commit_sha: str | None,
    store: RawSnapshotStore,
    source_subdir: str | None = None,
) -> list[RawSnapshotCopy]:
    copies: list[RawSnapshotCopy] = []
    manifest_root = repo_path / source_subdir if source_subdir else repo_path
    if not manifest_root.exists():
        raise FileNotFoundError(f"Source subdirectory does not exist: {manifest_root}")
    for relative_path, checksum in build_checksum_manifest(manifest_root):
        stored_relative_path = (
            str(PurePosixPath(source_subdir) / relative_path) if source_subdir else relative_path
        )
        object_key = raw_snapshot_object_key(
            source_key=source_key,
            snapshot_date=snapshot_date,
            source_commit_sha=source_commit_sha,
            relative_path=stored_relative_path,
        )
        storage_uri = store.put_file(manifest_root / relative_path, object_key)
        copies.append(
            RawSnapshotCopy(
                source_file_path=stored_relative_path,
                storage_uri=storage_uri,
                file_sha256=checksum,
            )
        )
    return copies


def raw_manifest_entries_from_copies(
    *,
    source_key: str,
    snapshot_date: date,
    source_commit_sha: str | None,
    copies: list[RawSnapshotCopy],
) -> list[RawManifestEntry]:
    return [
        RawManifestEntry.from_snapshot_copy(
            source_key=source_key,
            snapshot_date=snapshot_date,
            source_file_path=copy.source_file_path,
            storage_uri=copy.storage_uri,
            file_sha256=copy.file_sha256,
            source_commit_sha=source_commit_sha,
            notes="Raw third-party data; do not commit to Git or redistribute.",
        )
        for copy in copies
    ]
