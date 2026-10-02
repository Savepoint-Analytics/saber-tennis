from datetime import date

from tennis_sabermetrics.ingest.manifests import RawManifestEntry
from tennis_sabermetrics.ingest.postgres import raw_manifest_parameters


def test_raw_manifest_parameters_map_storage_uri_to_minio_uri() -> None:
    entry = RawManifestEntry(
        source_key="jeffsackmann_tennis_atp",
        snapshot_date=date(2026, 7, 15),
        source_file_path="atp_matches_2026.csv",
        storage_uri="s3://tennis-sabermetrics/raw/file.csv",
        file_sha256="abc",
        source_commit_sha="commit",
        row_count=12,
    )

    parameters = raw_manifest_parameters(entry)

    assert parameters["source_key"] == "jeffsackmann_tennis_atp"
    assert parameters["minio_uri"] == "s3://tennis-sabermetrics/raw/file.csv"
    assert parameters["row_count"] == 12

