import subprocess
from datetime import date

import pytest

from tennis_sabermetrics.ingest.git_sources import _git, sync_git_source


def test_sync_validates_minio_before_creating_external_root(tmp_path, monkeypatch) -> None:
    external_root = tmp_path / "missing" / "external"
    monkeypatch.setenv("TENNIS_SABERMETRICS_SKIP_DOTENV", "1")
    monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
    monkeypatch.delenv("MINIO_SECRET_KEY", raising=False)
    monkeypatch.delenv("SAVEPOINT_MINIO_ACCESS_KEY", raising=False)
    monkeypatch.delenv("SAVEPOINT_MINIO_SECRET_KEY", raising=False)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

    with pytest.raises(ValueError, match="Missing MinIO configuration"):
        sync_git_source(
            "jeffsackmann_tennis_atp",
            external_repos_root=external_root,
            snapshot_date=date(2026, 8, 4),
            copy_raw_to_minio=True,
            write_raw_manifest=True,
        )

    assert not external_root.exists()


def test_git_errors_include_stderr(monkeypatch) -> None:
    def fail_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=128,
            cmd=["git", "clone"],
            stderr="remote: Repository not found.",
        )

    monkeypatch.setattr(subprocess, "run", fail_run)

    with pytest.raises(ValueError, match="Repository not found"):
        _git(["clone", "https://example.invalid/repo"])
