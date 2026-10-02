"""Project configuration and source metadata."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, urlunparse

SOURCE_KEYS = (
    "jeffsackmann_tennis_atp",
    "jeffsackmann_tennis_wta",
    "jeffsackmann_match_charting",
    "jeffsackmann_slam_pointbypoint",
    "jeffsackmann_pointbypoint",
    "jeffsackmann_tennis_misc",
    "jeffsackmann_tennis_viz",
    "aneeshers_tennis_sackmann_archive",
    "tennisabstract_atp_elo",
    "tennisabstract_wta_elo",
    "tennis_data_co_uk_unverified",
    "tml_database_unverified",
)

FALLBACK_ARCHIVE_SOURCE_KEY = "aneeshers_tennis_sackmann_archive"


def load_dotenv(path: Path | str = ".env", *, override: bool = False) -> None:
    """Load simple KEY=VALUE pairs from a local dotenv file."""

    if os.getenv("TENNIS_SABERMETRICS_SKIP_DOTENV"):
        return
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", maxsplit=1)
        key = key.strip().removeprefix("export ").strip()
        value = value.strip().strip("'").strip('"')
        if override or key not in os.environ:
            os.environ[key] = value


def env_first(*keys: str, default: str | None = None) -> str | None:
    for key in keys:
        if value := os.getenv(key):
            return value
    return default


def normalize_minio_endpoint(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    api_port = os.getenv("MINIO_PORT")
    console_port = os.getenv("MINIO_CONSOLE_PORT")
    if not parsed.scheme or not parsed.hostname or not api_port:
        return endpoint
    if parsed.port and console_port and str(parsed.port) != console_port:
        return endpoint
    netloc = f"{parsed.hostname}:{api_port}"
    return urlunparse((parsed.scheme, netloc, parsed.path, "", "", ""))


@dataclass(frozen=True)
class ProjectPaths:
    """Filesystem locations used by local development and Savepoint-Lab."""

    raw_data_root: Path
    external_repos_root: Path
    bronze_data_root: Path

    @classmethod
    def from_env(cls) -> ProjectPaths:
        load_dotenv()
        return cls(
            raw_data_root=Path(os.getenv("RAW_DATA_ROOT", "/mnt/data/tennis/raw")),
            external_repos_root=Path(
                os.getenv("EXTERNAL_REPOS_ROOT", "/mnt/data/tennis/external")
            ),
            bronze_data_root=Path(os.getenv("BRONZE_DATA_ROOT", "/mnt/data/tennis/bronze")),
        )


@dataclass(frozen=True)
class MinioSettings:
    endpoint: str
    bucket: str
    access_key: str | None
    secret_key: str | None
    prefix: str | None = None

    @classmethod
    def from_env(cls) -> MinioSettings:
        load_dotenv()
        endpoint = env_first(
            "MINIO_ENDPOINT",
            "SAVEPOINT_MINIO_ENDPOINT",
            "S3_ENDPOINT",
            default="http://savepoint-lab.local:9000",
        ) or "http://savepoint-lab.local:9000"
        return cls(
            endpoint=normalize_minio_endpoint(endpoint),
            bucket=env_first(
                "MINIO_BUCKET",
                "SAVEPOINT_MINIO_BUCKET",
                "S3_BUCKET",
                default="tennis-sabermetrics",
            )
            or "tennis-sabermetrics",
            access_key=env_first(
                "MINIO_ACCESS_KEY",
                "SAVEPOINT_MINIO_ACCESS_KEY",
                "MINIO_ROOT_USER",
                "AWS_ACCESS_KEY_ID",
            ),
            secret_key=env_first(
                "MINIO_SECRET_KEY",
                "SAVEPOINT_MINIO_SECRET_KEY",
                "MINIO_ROOT_PASSWORD",
                "AWS_SECRET_ACCESS_KEY",
            ),
            prefix=env_first("MINIO_PREFIX", "SAVEPOINT_MINIO_PREFIX", "S3_PREFIX"),
        )

    def validate_for_write(self) -> None:
        missing = []
        if not self.endpoint:
            missing.append("MINIO_ENDPOINT")
        if not self.bucket:
            missing.append("MINIO_BUCKET")
        if not self.access_key:
            missing.append("MINIO_ACCESS_KEY or AWS_ACCESS_KEY_ID")
        if not self.secret_key:
            missing.append("MINIO_SECRET_KEY or AWS_SECRET_ACCESS_KEY")
        if missing:
            raise ValueError(f"Missing MinIO configuration: {', '.join(missing)}")


@dataclass(frozen=True)
class PostgresSettings:
    conninfo: str

    @classmethod
    def from_env(cls) -> PostgresSettings:
        load_dotenv()
        if database_url := env_first("POSTGRES_DSN", "DATABASE_URL"):
            return cls(conninfo=database_url)
        host = env_first(
            "POSTGRES_HOST",
            "SAVEPOINT_PG_HOST",
            "POSTGRESQL_DB_HOST",
            default="savepoint-lab.local",
        )
        port = env_first("POSTGRES_PORT", "SAVEPOINT_PG_PORT", "POSTGRESQL_DB_PORT", default="5432")
        dbname = env_first("POSTGRES_DB", "SAVEPOINT_PG_DB", "POSTGRESQL_DB_NAME", default="sports")
        user = env_first("POSTGRES_USER", "SAVEPOINT_PG_USER", "POSTGRESQL_DB_UID", default="alex")
        password = env_first(
            "POSTGRES_PASSWORD",
            "POSTGRES_PWD",
            "SAVEPOINT_PG_PWD",
            "POSTGRESQL_DB_PWD",
        )
        parts = [
            f"host={host}",
            f"port={port}",
            f"dbname={dbname}",
            f"user={user}",
        ]
        if password:
            parts.append(f"password={password}")
        return cls(conninfo=" ".join(parts))


@dataclass(frozen=True)
class SourceLicense:
    source_key: str
    source_name: str
    source_url: str
    license_name: str | None
    license_url: str | None
    attribution_required: bool
    non_commercial_only: bool
    share_alike_required: bool
    redistribution_allowed: bool | None
    commercial_use_allowed: bool | None
    status: str
    notes: str

    @property
    def is_verified_for_default_sync(self) -> bool:
        return self.status in {"target", "reference", "fallback"} and bool(self.license_name)


CANONICAL_GIT_SOURCES: dict[str, SourceLicense] = {
    "jeffsackmann_tennis_atp": SourceLicense(
        source_key="jeffsackmann_tennis_atp",
        source_name="Jeff Sackmann Tennis ATP",
        source_url="https://github.com/JeffSackmann/tennis_atp",
        license_name="CC BY-NC-SA 4.0",
        license_url="https://creativecommons.org/licenses/by-nc-sa/4.0/",
        attribution_required=True,
        non_commercial_only=True,
        share_alike_required=True,
        redistribution_allowed=False,
        commercial_use_allowed=False,
        status="target",
        notes="Canonical ATP match/ranking source.",
    ),
    "jeffsackmann_tennis_wta": SourceLicense(
        source_key="jeffsackmann_tennis_wta",
        source_name="Jeff Sackmann Tennis WTA",
        source_url="https://github.com/JeffSackmann/tennis_wta",
        license_name="CC BY-NC-SA 4.0",
        license_url="https://creativecommons.org/licenses/by-nc-sa/4.0/",
        attribution_required=True,
        non_commercial_only=True,
        share_alike_required=True,
        redistribution_allowed=False,
        commercial_use_allowed=False,
        status="target",
        notes="Canonical WTA match/ranking source.",
    ),
    "jeffsackmann_match_charting": SourceLicense(
        source_key="jeffsackmann_match_charting",
        source_name="Tennis Abstract Match Charting Project",
        source_url="https://github.com/JeffSackmann/tennis_MatchChartingProject",
        license_name="CC BY-NC-SA 4.0",
        license_url="https://creativecommons.org/licenses/by-nc-sa/4.0/",
        attribution_required=True,
        non_commercial_only=True,
        share_alike_required=True,
        redistribution_allowed=False,
        commercial_use_allowed=False,
        status="target",
        notes="Canonical charted point/shot data source.",
    ),
    "jeffsackmann_slam_pointbypoint": SourceLicense(
        source_key="jeffsackmann_slam_pointbypoint",
        source_name="Jeff Sackmann Grand Slam Point-by-Point",
        source_url="https://github.com/JeffSackmann/tennis_slam_pointbypoint",
        license_name="CC BY-NC-SA 4.0",
        license_url="https://creativecommons.org/licenses/by-nc-sa/4.0/",
        attribution_required=True,
        non_commercial_only=True,
        share_alike_required=True,
        redistribution_allowed=False,
        commercial_use_allowed=False,
        status="target",
        notes="Grand Slam point-level source with schema variation.",
    ),
    "jeffsackmann_pointbypoint": SourceLicense(
        source_key="jeffsackmann_pointbypoint",
        source_name="Jeff Sackmann Sequential Point-by-Point",
        source_url="https://github.com/JeffSackmann/tennis_pointbypoint",
        license_name="CC BY-NC-SA 4.0",
        license_url="https://creativecommons.org/licenses/by-nc-sa/4.0/",
        attribution_required=True,
        non_commercial_only=True,
        share_alike_required=True,
        redistribution_allowed=False,
        commercial_use_allowed=False,
        status="target",
        notes="Compact point-string source for simulation work.",
    ),
}

FALLBACK_GIT_SOURCES: dict[str, SourceLicense] = {
    FALLBACK_ARCHIVE_SOURCE_KEY: SourceLicense(
        source_key=FALLBACK_ARCHIVE_SOURCE_KEY,
        source_name="Aneeshers Tennis Sackmann Archive",
        source_url="https://github.com/Aneeshers/tennis-sackmann-archive",
        license_name="CC BY-NC-SA 4.0",
        license_url="https://creativecommons.org/licenses/by-nc-sa/4.0/",
        attribution_required=True,
        non_commercial_only=True,
        share_alike_required=True,
        redistribution_allowed=False,
        commercial_use_allowed=False,
        status="fallback",
        notes=(
            "Reviewed archival mirror for ATP/WTA/Slam point-by-point availability gaps. "
            "Use only with original Jeff Sackmann attribution and mirror provenance recorded."
        ),
    )
}

GIT_SOURCES: dict[str, SourceLicense] = {
    **CANONICAL_GIT_SOURCES,
    **FALLBACK_GIT_SOURCES,
}
