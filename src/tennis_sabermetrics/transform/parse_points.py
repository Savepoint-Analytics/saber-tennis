"""Parser for compact point-by-point strings."""

from __future__ import annotations

from dataclasses import dataclass

SERVER_WON = {"S", "A"}
RETURNER_WON = {"R", "D"}
IGNORED = {".", ";", "/", " "}


@dataclass(frozen=True)
class PointEvent:
    set_index: int
    game_index: int
    point_index: int
    code: str
    server_won: bool
    is_ace: bool = False
    is_double_fault: bool = False


def parse_point_sequence(sequence: str) -> tuple[PointEvent, ...]:
    """Parse `S/R/A/D` point strings with set/game separators."""

    events: list[PointEvent] = []
    set_index = 0
    game_index = 0
    point_index = 0

    for code in sequence:
        if code == ".":
            set_index += 1
            game_index = 0
            point_index = 0
            continue
        if code == ";":
            game_index += 1
            point_index = 0
            continue
        if code in {"/", " "}:
            continue
        if code not in SERVER_WON | RETURNER_WON:
            raise ValueError(f"Unknown point code {code!r}")

        events.append(
            PointEvent(
                set_index=set_index,
                game_index=game_index,
                point_index=point_index,
                code=code,
                server_won=code in SERVER_WON,
                is_ace=code == "A",
                is_double_fault=code == "D",
            )
        )
        point_index += 1

    return tuple(events)

