"""Leakage-safe pre-match feature construction."""

from __future__ import annotations

import csv
import hashlib
import math
from collections import deque
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field, fields
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any

from tennis_sabermetrics.config import PostgresSettings
from tennis_sabermetrics.models.elo import BlendedSurfaceEloModel, EloModel


@dataclass(frozen=True)
class RankingSnapshot:
    ranking_date: date
    tour: str
    player_id: str
    rank: int
    ranking_points: int | None = None


@dataclass(frozen=True)
class PlayerMatchStatLine:
    player_id: str
    first_serves_total: int | None = None
    first_serve_points_won: int | None = None
    second_serve_points_won: int | None = None
    aces: int | None = None
    double_faults: int | None = None

    @property
    def service_points_total(self) -> int | None:
        return self.first_serves_total

    @property
    def service_points_won(self) -> int | None:
        if self.first_serve_points_won is None or self.second_serve_points_won is None:
            return None
        return self.first_serve_points_won + self.second_serve_points_won


@dataclass(frozen=True)
class MatchFeatureInput:
    source_key: str
    tour: str
    match_id: str
    tournament_id: str | None
    match_date: date
    surface: str | None
    round: str | None
    best_of: int | None
    tournament_level: str | None
    draw_size: str | None
    winner_id: str
    loser_id: str
    winner_stats: PlayerMatchStatLine | None = None
    loser_stats: PlayerMatchStatLine | None = None


@dataclass
class _PlayerHistory:
    matches: int = 0
    wins: int = 0
    recent_results: deque[bool] = field(default_factory=lambda: deque(maxlen=10))
    last_match_date: date | None = None
    service_points_total: int = 0
    service_points_won: int = 0
    return_points_total: int = 0
    return_points_won: int = 0

    @property
    def win_pct(self) -> float | None:
        if self.matches == 0:
            return None
        return self.wins / self.matches

    @property
    def recent_10_win_pct(self) -> float | None:
        if not self.recent_results:
            return None
        return sum(self.recent_results) / len(self.recent_results)

    @property
    def serve_points_won_pct(self) -> float | None:
        if self.service_points_total == 0:
            return None
        return self.service_points_won / self.service_points_total

    @property
    def return_points_won_pct(self) -> float | None:
        if self.return_points_total == 0:
            return None
        return self.return_points_won / self.return_points_total


@dataclass(frozen=True)
class GoldMatchFeature:
    feature_row_id: str
    source_key: str
    tour: str
    match_id: str
    tournament_id: str | None
    match_date: date
    surface: str | None
    round: str | None
    best_of: int | None
    tournament_level: str | None
    draw_size: str | None
    player_a_id: str
    player_b_id: str
    player_a_won: bool
    player_a_rank: int | None
    player_b_rank: int | None
    player_a_ranking_points: int | None
    player_b_ranking_points: int | None
    player_a_rank_asof_date: date | None
    player_b_rank_asof_date: date | None
    rank_diff: int | None
    rank_log_diff: float | None
    player_a_overall_elo: float
    player_b_overall_elo: float
    overall_elo_diff: float
    player_a_surface_elo: float
    player_b_surface_elo: float
    surface_elo_diff: float
    player_a_prior_matches: int
    player_b_prior_matches: int
    player_a_prior_win_pct: float | None
    player_b_prior_win_pct: float | None
    prior_win_pct_diff: float | None
    player_a_recent_10_win_pct: float | None
    player_b_recent_10_win_pct: float | None
    recent_10_win_pct_diff: float | None
    player_a_days_since_last_match: int | None
    player_b_days_since_last_match: int | None
    rest_days_diff: int | None
    player_a_serve_points_won_pct_prior: float | None
    player_b_serve_points_won_pct_prior: float | None
    serve_points_won_pct_diff: float | None
    player_a_return_points_won_pct_prior: float | None
    player_b_return_points_won_pct_prior: float | None
    return_points_won_pct_diff: float | None
    max_feature_asof_date: date | None
    snapshot_date: date


GOLD_MATCH_FEATURE_COLUMNS = tuple(field.name for field in fields(GoldMatchFeature))


CREATE_GOLD_MATCH_FEATURES_SQL = """
create schema if not exists tennis;

create table if not exists tennis.gold_match_features_asof (
    feature_row_id text primary key,
    source_key text not null,
    tour text not null,
    match_id text not null,
    tournament_id text,
    match_date date not null,
    surface text,
    round text,
    best_of integer,
    tournament_level text,
    draw_size text,
    player_a_id text not null,
    player_b_id text not null,
    player_a_won boolean not null,
    player_a_rank integer,
    player_b_rank integer,
    player_a_ranking_points integer,
    player_b_ranking_points integer,
    player_a_rank_asof_date date,
    player_b_rank_asof_date date,
    rank_diff integer,
    rank_log_diff double precision,
    player_a_overall_elo double precision not null,
    player_b_overall_elo double precision not null,
    overall_elo_diff double precision not null,
    player_a_surface_elo double precision not null,
    player_b_surface_elo double precision not null,
    surface_elo_diff double precision not null,
    player_a_prior_matches integer not null,
    player_b_prior_matches integer not null,
    player_a_prior_win_pct double precision,
    player_b_prior_win_pct double precision,
    prior_win_pct_diff double precision,
    player_a_recent_10_win_pct double precision,
    player_b_recent_10_win_pct double precision,
    recent_10_win_pct_diff double precision,
    player_a_days_since_last_match integer,
    player_b_days_since_last_match integer,
    rest_days_diff integer,
    player_a_serve_points_won_pct_prior double precision,
    player_b_serve_points_won_pct_prior double precision,
    serve_points_won_pct_diff double precision,
    player_a_return_points_won_pct_prior double precision,
    player_b_return_points_won_pct_prior double precision,
    return_points_won_pct_diff double precision,
    max_feature_asof_date date,
    snapshot_date date not null,
    constraint gold_match_features_asof_no_future_features
        check (max_feature_asof_date is null or max_feature_asof_date < match_date)
);

alter table tennis.gold_match_features_asof
    add column if not exists tournament_level text;
alter table tennis.gold_match_features_asof
    add column if not exists draw_size text;

create index if not exists gold_match_features_asof_match_date_idx
    on tennis.gold_match_features_asof (match_date);
create index if not exists gold_match_features_asof_tour_date_idx
    on tennis.gold_match_features_asof (tour, match_date);
create index if not exists gold_match_features_asof_players_idx
    on tennis.gold_match_features_asof (player_a_id, player_b_id);
"""


POSTGRES_FEATURE_INDEX_SQL = """
create index if not exists bronze_matches_date_match_idx
    on tennis.bronze_matches (tourney_date, tour, match_id);
create index if not exists bronze_rankings_asof_idx
    on tennis.bronze_rankings (ranking_date, tour, player_id);
create index if not exists bronze_match_stats_match_player_idx
    on tennis.bronze_match_stats (tour, match_id, player_id);
"""


@dataclass(frozen=True)
class GoldFeatureBuildResult:
    table_name: str
    row_count: int


def _feature_id(match: MatchFeatureInput, player_a_id: str, player_b_id: str) -> str:
    key = "|".join(
        (
            match.source_key,
            match.tour,
            match.match_id,
            match.tournament_id or "",
            match.match_date.isoformat(),
            player_a_id,
            player_b_id,
        )
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def orient_match_players(match: MatchFeatureInput) -> tuple[str, str, bool]:
    """Deterministically orient players without using player IDs to choose side A."""

    key = "|".join(
        (
            match.source_key,
            match.tour,
            match.match_id,
            match.tournament_id or "",
            match.match_date.isoformat(),
        )
    )
    winner_is_player_a = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:2], 16) % 2 == 0
    if winner_is_player_a:
        return match.winner_id, match.loser_id, True
    return match.loser_id, match.winner_id, False


def _diff(left: float | int | None, right: float | int | None) -> float | int | None:
    if left is None or right is None:
        return None
    return left - right


def _days_since(match_date: date, prior_date: date | None) -> int | None:
    if prior_date is None:
        return None
    return (match_date - prior_date).days


def _int_diff(left: int | None, right: int | None) -> int | None:
    if left is None or right is None:
        return None
    return left - right


def _max_date(values: Iterable[date | None]) -> date | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return max(present)


class MatchFeatureState:
    """Stateful pre-match feature builder that updates only after each match date."""

    def __init__(self, *, snapshot_date: date, initial_elo: float = 1500.0) -> None:
        self.snapshot_date = snapshot_date
        self.overall_elo = EloModel(initial_rating=initial_elo)
        self.surface_elo = BlendedSurfaceEloModel(initial_rating=initial_elo)
        self.rankings: dict[tuple[str, str], RankingSnapshot] = {}
        self.history: dict[tuple[str, str], _PlayerHistory] = {}

    def apply_ranking(self, ranking: RankingSnapshot) -> None:
        self.rankings[(ranking.tour, ranking.player_id)] = ranking

    def _history_for(self, tour: str, player_id: str) -> _PlayerHistory:
        return self.history.setdefault((tour, player_id), _PlayerHistory())

    def build_for_date(self, matches: list[MatchFeatureInput]) -> list[GoldMatchFeature]:
        matches = _dedupe_matches(matches)
        features = [self._snapshot(match) for match in matches]
        for match in sorted(matches, key=lambda item: (item.tour, item.match_id)):
            self._apply_match_result(match)
        return features

    def _snapshot(self, match: MatchFeatureInput) -> GoldMatchFeature:
        player_a_id, player_b_id, player_a_won = orient_match_players(match)

        a_rank = self.rankings.get((match.tour, player_a_id))
        b_rank = self.rankings.get((match.tour, player_b_id))
        a_history = self._history_for(match.tour, player_a_id)
        b_history = self._history_for(match.tour, player_b_id)

        a_overall_elo = self.overall_elo.rating_for(player_a_id)
        b_overall_elo = self.overall_elo.rating_for(player_b_id)
        a_surface_elo = self.surface_elo.rating_for(player_a_id, match.surface).blended_rating
        b_surface_elo = self.surface_elo.rating_for(player_b_id, match.surface).blended_rating
        rank_diff = _diff(b_rank.rank if b_rank else None, a_rank.rank if a_rank else None)
        rank_log_diff = None
        if a_rank is not None and b_rank is not None:
            rank_log_diff = math.log((b_rank.rank + 1) / (a_rank.rank + 1))

        max_feature_asof_date = _max_date(
            (
                a_rank.ranking_date if a_rank else None,
                b_rank.ranking_date if b_rank else None,
                a_history.last_match_date,
                b_history.last_match_date,
            )
        )

        return GoldMatchFeature(
            feature_row_id=_feature_id(match, player_a_id, player_b_id),
            source_key=match.source_key,
            tour=match.tour,
            match_id=match.match_id,
            tournament_id=match.tournament_id,
            match_date=match.match_date,
            surface=match.surface,
            round=match.round,
            best_of=match.best_of,
            tournament_level=match.tournament_level,
            draw_size=match.draw_size,
            player_a_id=player_a_id,
            player_b_id=player_b_id,
            player_a_won=player_a_won,
            player_a_rank=a_rank.rank if a_rank else None,
            player_b_rank=b_rank.rank if b_rank else None,
            player_a_ranking_points=a_rank.ranking_points if a_rank else None,
            player_b_ranking_points=b_rank.ranking_points if b_rank else None,
            player_a_rank_asof_date=a_rank.ranking_date if a_rank else None,
            player_b_rank_asof_date=b_rank.ranking_date if b_rank else None,
            rank_diff=rank_diff if isinstance(rank_diff, int) else None,
            rank_log_diff=rank_log_diff,
            player_a_overall_elo=a_overall_elo,
            player_b_overall_elo=b_overall_elo,
            overall_elo_diff=a_overall_elo - b_overall_elo,
            player_a_surface_elo=a_surface_elo,
            player_b_surface_elo=b_surface_elo,
            surface_elo_diff=a_surface_elo - b_surface_elo,
            player_a_prior_matches=a_history.matches,
            player_b_prior_matches=b_history.matches,
            player_a_prior_win_pct=a_history.win_pct,
            player_b_prior_win_pct=b_history.win_pct,
            prior_win_pct_diff=_diff(a_history.win_pct, b_history.win_pct),
            player_a_recent_10_win_pct=a_history.recent_10_win_pct,
            player_b_recent_10_win_pct=b_history.recent_10_win_pct,
            recent_10_win_pct_diff=_diff(
                a_history.recent_10_win_pct, b_history.recent_10_win_pct
            ),
            player_a_days_since_last_match=_days_since(match.match_date, a_history.last_match_date),
            player_b_days_since_last_match=_days_since(match.match_date, b_history.last_match_date),
            rest_days_diff=_int_diff(
                _days_since(match.match_date, a_history.last_match_date),
                _days_since(match.match_date, b_history.last_match_date),
            ),
            player_a_serve_points_won_pct_prior=a_history.serve_points_won_pct,
            player_b_serve_points_won_pct_prior=b_history.serve_points_won_pct,
            serve_points_won_pct_diff=_diff(
                a_history.serve_points_won_pct, b_history.serve_points_won_pct
            ),
            player_a_return_points_won_pct_prior=a_history.return_points_won_pct,
            player_b_return_points_won_pct_prior=b_history.return_points_won_pct,
            return_points_won_pct_diff=_diff(
                a_history.return_points_won_pct, b_history.return_points_won_pct
            ),
            max_feature_asof_date=max_feature_asof_date,
            snapshot_date=self.snapshot_date,
        )

    def _apply_match_result(self, match: MatchFeatureInput) -> None:
        self.overall_elo.predict_then_update(_elo_match(match))
        self.surface_elo.predict_then_update(_elo_match(match))

        winner_history = self._history_for(match.tour, match.winner_id)
        loser_history = self._history_for(match.tour, match.loser_id)
        winner_history.matches += 1
        winner_history.wins += 1
        winner_history.recent_results.append(True)
        winner_history.last_match_date = match.match_date
        loser_history.matches += 1
        loser_history.recent_results.append(False)
        loser_history.last_match_date = match.match_date
        _apply_serve_return_stats(winner_history, loser_history, match.winner_stats, match.loser_stats)


def _elo_match(match: MatchFeatureInput) -> Any:
    from tennis_sabermetrics.models.elo import MatchResult

    return MatchResult(
        match_date=match.match_date,
        winner_id=match.winner_id,
        loser_id=match.loser_id,
        surface=match.surface,
    )


def _apply_serve_return_stats(
    winner_history: _PlayerHistory,
    loser_history: _PlayerHistory,
    winner_stats: PlayerMatchStatLine | None,
    loser_stats: PlayerMatchStatLine | None,
) -> None:
    _apply_service_stats(winner_history, winner_stats)
    _apply_service_stats(loser_history, loser_stats)
    _apply_return_stats(winner_history, loser_stats)
    _apply_return_stats(loser_history, winner_stats)


def _apply_service_stats(history: _PlayerHistory, stats: PlayerMatchStatLine | None) -> None:
    if stats is None or stats.service_points_total is None or stats.service_points_won is None:
        return
    history.service_points_total += stats.service_points_total
    history.service_points_won += stats.service_points_won


def _apply_return_stats(history: _PlayerHistory, opponent_stats: PlayerMatchStatLine | None) -> None:
    if (
        opponent_stats is None
        or opponent_stats.service_points_total is None
        or opponent_stats.service_points_won is None
    ):
        return
    history.return_points_total += opponent_stats.service_points_total
    history.return_points_won += opponent_stats.service_points_total - opponent_stats.service_points_won


def build_match_features_asof(
    matches: Iterable[MatchFeatureInput],
    rankings: Iterable[RankingSnapshot],
    *,
    snapshot_date: date,
) -> list[GoldMatchFeature]:
    """Build pre-match features with rankings and match state frozen by match date."""

    state = MatchFeatureState(snapshot_date=snapshot_date)
    ranking_iter = iter(sorted(rankings, key=lambda item: item.ranking_date))
    next_ranking = next(ranking_iter, None)
    output: list[GoldMatchFeature] = []
    for match_date, date_matches in _group_matches_by_date(matches):
        while next_ranking is not None and next_ranking.ranking_date < match_date:
            state.apply_ranking(next_ranking)
            next_ranking = next(ranking_iter, None)
        output.extend(state.build_for_date(date_matches))
    return output


def _group_matches_by_date(
    matches: Iterable[MatchFeatureInput],
) -> Iterator[tuple[date, list[MatchFeatureInput]]]:
    current_date: date | None = None
    batch: list[MatchFeatureInput] = []
    for match in sorted(matches, key=lambda item: (item.match_date, item.tour, item.match_id)):
        if current_date is None:
            current_date = match.match_date
        if match.match_date != current_date:
            yield current_date, batch
            current_date = match.match_date
            batch = []
        batch.append(match)
    if current_date is not None:
        yield current_date, batch


def _dedupe_matches(matches: list[MatchFeatureInput]) -> list[MatchFeatureInput]:
    seen: set[tuple[str, str, str, str | None, date, str, str]] = set()
    output: list[MatchFeatureInput] = []
    for match in matches:
        key = (
            match.source_key,
            match.tour,
            match.match_id,
            match.tournament_id,
            match.match_date,
            match.winner_id,
            match.loser_id,
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(match)
    return output


def create_postgres_feature_indexes(conninfo: str | None = None) -> None:
    import psycopg

    with psycopg.connect(conninfo or PostgresSettings.from_env().conninfo) as connection:
        with connection.cursor() as cursor:
            cursor.execute(POSTGRES_FEATURE_INDEX_SQL)
        connection.commit()


def build_gold_match_features_postgres(
    *,
    snapshot_date: date,
    start_date: date | None = None,
    end_date: date | None = None,
    conninfo: str | None = None,
    replace: bool = True,
) -> GoldFeatureBuildResult:
    """Build `tennis.gold_match_features_asof` from PostgreSQL silver models."""

    import psycopg

    create_postgres_feature_indexes(conninfo)
    with psycopg.connect(conninfo or PostgresSettings.from_env().conninfo) as write_connection:
        with write_connection.cursor() as cursor:
            cursor.execute(CREATE_GOLD_MATCH_FEATURES_SQL)
            if replace:
                cursor.execute("truncate table tennis.gold_match_features_asof")
        write_connection.commit()

    row_count = 0
    state = MatchFeatureState(snapshot_date=snapshot_date)
    with (
        psycopg.connect(conninfo or PostgresSettings.from_env().conninfo) as read_connection,
        psycopg.connect(conninfo or PostgresSettings.from_env().conninfo) as write_connection,
    ):
        ranking_cursor = read_connection.cursor(name="gold_match_features_rankings")
        ranking_cursor.execute(_ranking_sql(end_date), _ranking_params(end_date))
        ranking_iter = iter(ranking_cursor)
        next_ranking = _ranking_from_row(next(ranking_iter, None))

        match_cursor = read_connection.cursor(name="gold_match_features_matches")
        match_cursor.execute(_match_sql(start_date, end_date), _match_params(start_date, end_date))

        current_date: date | None = None
        batch: list[MatchFeatureInput] = []
        for row in match_cursor:
            match = _match_from_row(row)
            if current_date is None:
                current_date = match.match_date
            if match.match_date != current_date:
                next_ranking = _apply_rankings_before_date(
                    state, ranking_iter, next_ranking, current_date
                )
                row_count += _copy_features(write_connection, state.build_for_date(batch))
                current_date = match.match_date
                batch = []
            batch.append(match)

        if current_date is not None:
            next_ranking = _apply_rankings_before_date(
                state, ranking_iter, next_ranking, current_date
            )
            row_count += _copy_features(write_connection, state.build_for_date(batch))

        write_connection.commit()

    return GoldFeatureBuildResult(table_name="tennis.gold_match_features_asof", row_count=row_count)


def _ranking_sql(end_date: date | None) -> str:
    sql = """
        select ranking_date, tour, player_id, rank, ranking_points
        from tennis.bronze_rankings
        where ranking_date is not null
          and player_id is not null
          and rank is not null
    """
    if end_date is not None:
        sql += " and ranking_date < %s"
    sql += " order by ranking_date, tour, player_id, rank"
    return sql


def _ranking_params(end_date: date | None) -> tuple[date, ...]:
    return (end_date,) if end_date is not None else ()


def _match_sql(start_date: date | None, end_date: date | None) -> str:
    conditions = ["m.tourney_date is not null"]
    if start_date is not None:
        conditions.append("m.tourney_date >= %s")
    if end_date is not None:
        conditions.append("m.tourney_date <= %s")
    where_sql = " and ".join(conditions)
    return f"""
        select
            m.source_key,
            m.tour,
            m.match_id,
            m.tourney_id,
            m.tourney_date,
            m.surface,
            m.round,
            m.best_of,
            t.tourney_level,
            t.draw_size,
            m.winner_id,
            m.loser_id,
            ws.first_serves_total,
            ws.first_serve_points_won,
            ws.second_serve_points_won,
            ws.aces,
            ws.double_faults,
            ls.first_serves_total,
            ls.first_serve_points_won,
            ls.second_serve_points_won,
            ls.aces,
            ls.double_faults
        from tennis.bronze_matches m
        left join tennis.bronze_match_stats ws
            on ws.tour = m.tour
           and ws.match_id = m.match_id
           and ws.player_id = m.winner_id
        left join tennis.bronze_match_stats ls
            on ls.tour = m.tour
           and ls.match_id = m.match_id
           and ls.player_id = m.loser_id
        left join (
            select
                source_key,
                tour,
                tourney_id,
                tourney_date,
                max(tourney_level) as tourney_level,
                max(draw_size) as draw_size
            from tennis.bronze_tournaments
            group by source_key, tour, tourney_id, tourney_date
        ) t
            on t.tour = m.tour
           and t.tourney_id = m.tourney_id
           and t.tourney_date = m.tourney_date
           and t.source_key = m.source_key
        where {where_sql}
          and m.winner_id is not null
          and m.loser_id is not null
          and m.winner_id <> m.loser_id
        order by m.tourney_date, m.tour, m.match_id
    """


def _match_params(start_date: date | None, end_date: date | None) -> tuple[date, ...]:
    params: list[date] = []
    if start_date is not None:
        params.append(start_date)
    if end_date is not None:
        params.append(end_date)
    return tuple(params)


def _ranking_from_row(row: Any | None) -> RankingSnapshot | None:
    if row is None:
        return None
    return RankingSnapshot(
        ranking_date=row[0],
        tour=row[1],
        player_id=str(row[2]),
        rank=row[3],
        ranking_points=row[4],
    )


def _apply_rankings_before_date(
    state: MatchFeatureState,
    ranking_iter: Iterator[Any],
    next_ranking: RankingSnapshot | None,
    match_date: date,
) -> RankingSnapshot | None:
    while next_ranking is not None and next_ranking.ranking_date < match_date:
        state.apply_ranking(next_ranking)
        next_ranking = _ranking_from_row(next(ranking_iter, None))
    return next_ranking


def _match_from_row(row: Any) -> MatchFeatureInput:
    winner_stats = _stats_from_row(row[10], row[12:17])
    loser_stats = _stats_from_row(row[11], row[17:22])
    return MatchFeatureInput(
        source_key=row[0],
        tour=row[1],
        match_id=row[2],
        tournament_id=row[3],
        match_date=row[4],
        surface=row[5],
        round=row[6],
        best_of=row[7],
        tournament_level=row[8],
        draw_size=row[9],
        winner_id=row[10],
        loser_id=row[11],
        winner_stats=winner_stats,
        loser_stats=loser_stats,
    )


def _stats_from_row(player_id: str, values: Any) -> PlayerMatchStatLine | None:
    if all(value is None for value in values):
        return None
    return PlayerMatchStatLine(
        player_id=player_id,
        first_serves_total=values[0],
        first_serve_points_won=values[1],
        second_serve_points_won=values[2],
        aces=values[3],
        double_faults=values[4],
    )


def _copy_features(connection: Any, features: list[GoldMatchFeature]) -> int:
    if not features:
        return 0
    output = StringIO()
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    for feature in features:
        writer.writerow([_copy_value(getattr(feature, column)) for column in GOLD_MATCH_FEATURE_COLUMNS])
    column_sql = ", ".join(GOLD_MATCH_FEATURE_COLUMNS)
    with connection.cursor() as cursor:
        with cursor.copy(
            f"copy tennis.gold_match_features_asof ({column_sql}) "
            "from stdin with (format csv, delimiter E'\\t', null '\\N')"
        ) as copy:
            copy.write(output.getvalue())
    connection.commit()
    return len(features)


def _copy_value(value: object) -> object:
    if value is None:
        return "\\N"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, date):
        return value.isoformat()
    return value


def write_features_csv(features: Iterable[GoldMatchFeature], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(GOLD_MATCH_FEATURE_COLUMNS)
        for feature in features:
            writer.writerow([getattr(feature, column) for column in GOLD_MATCH_FEATURE_COLUMNS])
            count += 1
    return count
