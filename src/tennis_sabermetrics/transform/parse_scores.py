"""Tennis score parsing helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass

SET_RE = re.compile(
    r"^(?P<winner>\d+)-(?P<loser>\d+)(?:\((?P<tiebreak_winner>\d+-)?(?P<tiebreak>\d+)\))?$"
)
STATUS_TOKENS = {
    "ABANDONED": "not_completed",
    "ABD": "not_completed",
    "DEF": "default",
    "DEFAULT": "default",
    "RET": "retirement",
    "RETIRED": "retirement",
    "W/O": "walkover",
    "WO": "walkover",
    "WALKOVER": "walkover",
}


@dataclass(frozen=True)
class ParsedSet:
    winner_games: int
    loser_games: int
    tiebreak_loser_points: int | None = None
    tiebreak_winner_points: int | None = None

    @property
    def went_to_tiebreak(self) -> bool:
        return self.tiebreak_loser_points is not None or (self.winner_games, self.loser_games) == (7, 6)

    @property
    def is_match_tiebreak(self) -> bool:
        return self.winner_games >= 10 and self.winner_games - self.loser_games >= 2


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
    tokens = score.strip().replace("[", "").replace("]", "").replace(",", " ").split()
    sets: list[ParsedSet] = []
    status = "completed"

    for token in tokens:
        normalized = token.strip().strip(".").upper()
        if normalized in STATUS_TOKENS:
            status = STATUS_TOKENS[normalized]
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
                tiebreak_winner_points=(
                    int(match.group("tiebreak_winner").rstrip("-"))
                    if match.group("tiebreak_winner")
                    else None
                ),
            )
        )

    return ParsedScore(sets=tuple(sets), status=status, raw=raw)
