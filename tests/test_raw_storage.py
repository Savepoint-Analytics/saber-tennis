from datetime import date

from tennis_sabermetrics.config import MinioSettings
from tennis_sabermetrics.ingest.storage import (
    LocalRawSnapshotStore,
    MinioRawSnapshotStore,
    copy_raw_snapshot,
    raw_manifest_entries_from_copies,
    raw_snapshot_object_key,
)


def test_raw_snapshot_object_key_uses_license_safe_layout() -> None:
    key = raw_snapshot_object_key(
        source_key="jeffsackmann_tennis_atp",
        snapshot_date=date(2026, 7, 15),
        source_commit_sha="abc123",
        relative_path="atp_matches_2026.csv",
    )

    assert (
        key
        == "raw/jeffsackmann_tennis_atp/snapshot_date=2026-07-15/commit=abc123/atp_matches_2026.csv"
    )


def test_copy_raw_snapshot_skips_git_and_builds_manifest_entries(tmp_path) -> None:
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    (repo_path / "atp_matches_2026.csv").write_text("winner,loser\nA,B\n", encoding="utf-8")
    git_dir = repo_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("not copied", encoding="utf-8")

    store = LocalRawSnapshotStore(tmp_path / "raw_store")
    copies = copy_raw_snapshot(
        source_key="jeffsackmann_tennis_atp",
        repo_path=repo_path,
        snapshot_date=date(2026, 7, 15),
        source_commit_sha="abc123",
        store=store,
    )
    entries = raw_manifest_entries_from_copies(
        source_key="jeffsackmann_tennis_atp",
        snapshot_date=date(2026, 7, 15),
        source_commit_sha="abc123",
        copies=copies,
    )

    assert len(copies) == 1
    assert copies[0].source_file_path == "atp_matches_2026.csv"
    assert "raw/jeffsackmann_tennis_atp/" in copies[0].storage_uri
    assert entries[0].storage_uri == copies[0].storage_uri
    assert entries[0].source_commit_sha == "abc123"


def test_copy_raw_snapshot_can_filter_source_subdir(tmp_path) -> None:
    repo_path = tmp_path / "repo"
    atp_path = repo_path / "atp"
    wta_path = repo_path / "wta"
    atp_path.mkdir(parents=True)
    wta_path.mkdir()
    (atp_path / "atp_matches_2026.csv").write_text("winner,loser\nA,B\n", encoding="utf-8")
    (wta_path / "wta_matches_2026.csv").write_text("winner,loser\nC,D\n", encoding="utf-8")

    store = LocalRawSnapshotStore(tmp_path / "raw_store")
    copies = copy_raw_snapshot(
        source_key="aneeshers_tennis_sackmann_archive",
        repo_path=repo_path,
        snapshot_date=date(2026, 8, 24),
        source_commit_sha="archive123",
        store=store,
        source_subdir="atp",
    )

    assert len(copies) == 1
    assert copies[0].source_file_path == "atp/atp_matches_2026.csv"
    assert "wta_matches" not in copies[0].storage_uri


def test_minio_store_applies_prefix(monkeypatch, tmp_path) -> None:
    writes = []

    class FakeOutput:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def write(self, data):
            return len(data)

    class FakeS3:
        def __init__(self, **kwargs):
            pass

        def open_output_stream(self, destination):
            writes.append(destination)
            return FakeOutput()

    monkeypatch.setattr("pyarrow.fs.S3FileSystem", FakeS3)
    source_path = tmp_path / "file.csv"
    source_path.write_text("a,b\n1,2\n", encoding="utf-8")

    store = MinioRawSnapshotStore(
        MinioSettings(
            endpoint="http://minio.local:9000",
            bucket="sabermetrics",
            access_key="access",
            secret_key="secret",
            prefix="tennis",
        )
    )

    uri = store.put_file(source_path, "raw/source/file.csv")

    assert writes == ["sabermetrics/tennis/raw/source/file.csv"]
    assert uri == "s3://sabermetrics/tennis/raw/source/file.csv"
