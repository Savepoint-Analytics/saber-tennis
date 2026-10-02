import os

import pytest

from tennis_sabermetrics.cli import main
from tennis_sabermetrics.config import (
    MinioSettings,
    PostgresSettings,
    load_dotenv,
    normalize_minio_endpoint,
)


def test_load_dotenv_sets_missing_values(tmp_path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("EXAMPLE_KEY='example-value'\n", encoding="utf-8")
    monkeypatch.delenv("EXAMPLE_KEY", raising=False)

    load_dotenv(env_path)

    assert os.environ["EXAMPLE_KEY"] == "example-value"


def test_postgres_settings_support_savepoint_aliases(monkeypatch) -> None:
    monkeypatch.setenv("TENNIS_SABERMETRICS_SKIP_DOTENV", "1")
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_HOST", raising=False)
    monkeypatch.delenv("POSTGRES_PORT", raising=False)
    monkeypatch.delenv("POSTGRES_DB", raising=False)
    monkeypatch.delenv("POSTGRES_USER", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    monkeypatch.delenv("POSTGRESQL_DB_HOST", raising=False)
    monkeypatch.delenv("POSTGRESQL_DB_PORT", raising=False)
    monkeypatch.delenv("POSTGRESQL_DB_NAME", raising=False)
    monkeypatch.delenv("POSTGRESQL_DB_UID", raising=False)
    monkeypatch.delenv("POSTGRESQL_DB_PWD", raising=False)
    monkeypatch.setenv("SAVEPOINT_PG_HOST", "db.local")
    monkeypatch.setenv("SAVEPOINT_PG_PORT", "5433")
    monkeypatch.setenv("SAVEPOINT_PG_USER", "alex")
    monkeypatch.setenv("SAVEPOINT_PG_PWD", "secret")
    monkeypatch.setenv("SAVEPOINT_PG_DB", "sports")

    settings = PostgresSettings.from_env()

    assert "host=db.local" in settings.conninfo
    assert "port=5433" in settings.conninfo
    assert "dbname=sports" in settings.conninfo
    assert "user=alex" in settings.conninfo
    assert "password=secret" in settings.conninfo


def test_minio_settings_require_write_credentials() -> None:
    settings = MinioSettings(
        endpoint="http://savepoint-lab.local:9000",
        bucket="tennis-sabermetrics",
        access_key=None,
        secret_key=None,
    )

    with pytest.raises(ValueError, match="Missing MinIO configuration"):
        settings.validate_for_write()


def test_minio_settings_support_savepoint_aliases(monkeypatch) -> None:
    monkeypatch.setenv("TENNIS_SABERMETRICS_SKIP_DOTENV", "1")
    monkeypatch.delenv("MINIO_ENDPOINT", raising=False)
    monkeypatch.delenv("MINIO_BUCKET", raising=False)
    monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
    monkeypatch.delenv("MINIO_SECRET_KEY", raising=False)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.setenv("SAVEPOINT_MINIO_ENDPOINT", "http://minio.local:9000")
    monkeypatch.setenv("SAVEPOINT_MINIO_BUCKET", "tennis")
    monkeypatch.setenv("SAVEPOINT_MINIO_ACCESS_KEY", "access")
    monkeypatch.setenv("SAVEPOINT_MINIO_SECRET_KEY", "secret")

    settings = MinioSettings.from_env()

    assert settings.endpoint == "http://minio.local:9000"
    assert settings.bucket == "tennis"
    assert settings.access_key == "access"
    assert settings.secret_key == "secret"


def test_normalize_minio_endpoint_replaces_console_port(monkeypatch) -> None:
    monkeypatch.setenv("MINIO_PORT", "9000")
    monkeypatch.setenv("MINIO_CONSOLE_PORT", "9001")

    assert normalize_minio_endpoint("http://minio.local:9001") == "http://minio.local:9000"


def test_cli_reports_configuration_errors_without_traceback(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TENNIS_SABERMETRICS_SKIP_DOTENV", "1")
    monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
    monkeypatch.delenv("MINIO_SECRET_KEY", raising=False)
    monkeypatch.delenv("SAVEPOINT_MINIO_ACCESS_KEY", raising=False)
    monkeypatch.delenv("SAVEPOINT_MINIO_SECRET_KEY", raising=False)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "sync-sources",
                "--source",
                "jeffsackmann_tennis_atp",
                "--snapshot-date",
                "2026-08-04",
                "--copy-raw-to-minio",
            ]
        )

    assert exc_info.value.code == 1
    assert "Missing MinIO configuration" in capsys.readouterr().err
