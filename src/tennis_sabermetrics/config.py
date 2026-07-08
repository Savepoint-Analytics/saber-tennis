"""Project configuration and source metadata."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

SOURCE_KEYS = (
    "jeffsackmann_tennis_atp",
    "jeffsackmann_tennis_wta",
    "jeffsackmann_match_charting",
    "jeffsackmann_slam_pointbypoint",
    "jeffsackmann_pointbypoint",
    "jeffsackmann_tennis_misc",
    "jeffsackmann_tennis_viz",
    "tennisabstract_atp_elo",
    "tennisabstract_wta_elo",
    "tennis_data_co_uk_unverified",
    "tml_database_unverified",
)


@dataclass(frozen=True)
class ProjectPaths:
    """Filesystem locations used by local development and Savepoint-Lab."""

    raw_data_root: Path
    external_repos_root: Path

    @classmethod
    def from_env(cls) -> ProjectPaths:
        return cls(
            raw_data_root=Path(os.getenv("RAW_DATA_ROOT", "/mnt/data/tennis/raw")),
            external_repos_root=Path(
                os.getenv("EXTERNAL_REPOS_ROOT", "/mnt/data/tennis/external")
            ),
        )


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
        return self.status in {"target", "reference"} and bool(self.license_name)


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

