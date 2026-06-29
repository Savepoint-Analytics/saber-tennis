from pathlib import Path


def test_no_bulk_raw_data_directories_exist() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    forbidden_paths = [
        repo_root / "data" / "raw",
        repo_root / "data" / "bronze",
        repo_root / "data" / "silver",
        repo_root / "data" / "gold",
        repo_root / "data" / "external",
    ]

    assert not any(path.exists() for path in forbidden_paths)

