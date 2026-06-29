"""Tennis score parsing helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass


SET_RE = re.compile(r"^(?P<winner>\d+)-(?P<loser>\d+)(?:\((?P<tiebreak>\d+)\))?$")
STATUS_TOKENS = {"RET", "W/O", "WO", "DEF", "ABD", "Default"}


@dataclass(frozen=True)
class ParsedSet:
    winner_games: int
    loser_games: int
    tiebreak_loser_points: int | None = None

    @property
    def went_to_tiebreak(self) -> bool:
        return self.tiebreak_loser_points is not None or (self.winner_games, self.loser_games) == (7, 6)


@dataclass(frozen=True)
class ParsedScore:
    sets: tuple[ParsedSet, ...]
    status: str = "completed"
    raw: str = ""

    @property
    def best_of(self) -> int:
        return 5 if len(self.sets) > 3 else 3


def parse_match_score(score: str) -> ParsedScore:
    """Parse common winner-perspective match scores from Tennis Abstract-style data."""

    raw = score
    tokens = score.strip().replace("[", "").replace("]", "").split()
    sets: list[ParsedSet] = []
    status = "completed"

    for token in tokens:
        normalized = token.strip()
        if normalized in STATUS_TOKENS:
            status = "walkover" if normalized in {"W/O", "WO"} else "not_completed"
            continue
        match = SET_RE.match(normalized)
        if not match:
            raise ValueError(f"Could not parse score token {normalized!r} from {raw!r}")
        sets.append(
            ParsedSet(
                winner_games=int(match.group("winner")),
                loser_games=int(match.group("loser")),
                tiebreak_loser_points=(
                    int(match.group("tiebreak")) if match.group("tiebreak") else None
                ),
            )
        )

    return ParsedScore(sets=tuple(sets), status=status, raw=raw)

