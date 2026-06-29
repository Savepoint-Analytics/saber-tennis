"""Canonical Git source acquisition planning."""

from __future__ import annotations

from dataclasses import dataclass

from tennis_sabermetrics.config import CANONICAL_GIT_SOURCES, SourceLicense


@dataclass(frozen=True)
class SourceSyncPlanItem:
    source: SourceLicense
    action: str


def plan_source_sync(
    source_keys: tuple[str, ...],
    *,
    dry_run: bool,
    allow_unverified_source: bool = False,
) -> list[SourceSyncPlanItem]:
    """Return an acquisition plan and refuse missing license metadata by default."""

    items: list[SourceSyncPlanItem] = []
    for source_key in source_keys:
        try:
            source = CANONICAL_GIT_SOURCES[source_key]
        except KeyError as exc:
            raise ValueError(f"Unknown canonical source key: {source_key}") from exc

        if not allow_unverified_source and not source.is_verified_for_default_sync:
            raise ValueError(
                f"Source {source_key} lacks verified license metadata; "
                "pass --allow-unverified-source only for isolated/private evaluation."
            )

        action = "plan-clone-or-fetch" if dry_run else "clone-or-fetch"
        items.append(SourceSyncPlanItem(source=source, action=action))

    return items

