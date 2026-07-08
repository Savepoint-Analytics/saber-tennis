from tennis_sabermetrics.ingest.manifests import build_checksum_manifest


def test_checksum_manifest_skips_git_directory(tmp_path) -> None:
    (tmp_path / "source.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("private git internals", encoding="utf-8")

    manifest = build_checksum_manifest(tmp_path)

    assert [path for path, _checksum in manifest] == ["source.csv"]
