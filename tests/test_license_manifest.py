from tennis_sabermetrics.config import CANONICAL_GIT_SOURCES, GIT_SOURCES, SOURCE_KEYS
from tennis_sabermetrics.ingest.git_sources import plan_source_sync, repo_dir_name


def test_required_source_keys_are_declared() -> None:
    assert "jeffsackmann_tennis_atp" in SOURCE_KEYS
    assert "jeffsackmann_tennis_wta" in SOURCE_KEYS
    assert "aneeshers_tennis_sackmann_archive" in SOURCE_KEYS
    assert "tennis_data_co_uk_unverified" in SOURCE_KEYS


def test_default_git_sources_have_license_metadata() -> None:
    for source in CANONICAL_GIT_SOURCES.values():
        assert source.license_name
        assert source.non_commercial_only
        assert source.attribution_required


def test_dry_run_sync_plan_uses_canonical_sources() -> None:
    plan = plan_source_sync(("jeffsackmann_tennis_atp",), dry_run=True)

    assert len(plan) == 1
    assert plan[0].action == "plan-clone-or-fetch"
    assert plan[0].source.source_url == "https://github.com/JeffSackmann/tennis_atp"


def test_fallback_archive_is_not_a_default_git_source() -> None:
    assert "aneeshers_tennis_sackmann_archive" not in CANONICAL_GIT_SOURCES
    assert "aneeshers_tennis_sackmann_archive" in GIT_SOURCES


def test_repo_dir_name_uses_url_stem() -> None:
    source = CANONICAL_GIT_SOURCES["jeffsackmann_tennis_atp"]

    assert repo_dir_name(source) == "tennis_atp"
