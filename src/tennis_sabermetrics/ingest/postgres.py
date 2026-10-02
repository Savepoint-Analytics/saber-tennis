"""PostgreSQL persistence for source metadata."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from tennis_sabermetrics.config import PostgresSettings
from tennis_sabermetrics.ingest.manifests import RawManifestEntry

RAW_MANIFEST_INSERT_SQL = """
insert into tennis.raw_manifest (
    source_key,
    snapshot_date,
    source_commit_sha,
    source_file_path,
    minio_uri,
    file_sha256,
    row_count,
    acquired_at,
    notes
) values (
    %(source_key)s,
    %(snapshot_date)s,
    %(source_commit_sha)s,
    %(source_file_path)s,
    %(minio_uri)s,
    %(file_sha256)s,
    %(row_count)s,
    %(acquired_at)s,
    %(notes)s
)
on conflict (source_key, snapshot_date, source_file_path, file_sha256) do nothing
"""


def raw_manifest_parameters(entry: RawManifestEntry) -> dict[str, object]:
    return {
        "source_key": entry.source_key,
        "snapshot_date": entry.snapshot_date,
        "source_commit_sha": entry.source_commit_sha,
        "source_file_path": entry.source_file_path,
        "minio_uri": entry.storage_uri,
        "file_sha256": entry.file_sha256,
        "row_count": entry.row_count,
        "acquired_at": entry.acquired_at,
        "notes": entry.notes,
    }


@dataclass(frozen=True)
class RawManifestWriter:
    conninfo: str

    @classmethod
    def from_env(cls) -> RawManifestWriter:
        return cls(conninfo=PostgresSettings.from_env().conninfo)

    def insert_entries(self, entries: Iterable[RawManifestEntry]) -> int:
        import psycopg

        parameters = [raw_manifest_parameters(entry) for entry in entries]
        if not parameters:
            return 0

        with psycopg.connect(self.conninfo) as connection:
            with connection.cursor() as cursor:
                cursor.executemany(RAW_MANIFEST_INSERT_SQL, parameters)
            connection.commit()
        return len(parameters)


def execute_sql_file(sql_path: str) -> None:
    import psycopg

    sql = open(sql_path, encoding="utf-8").read()
    with psycopg.connect(PostgresSettings.from_env().conninfo) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)
        connection.commit()
