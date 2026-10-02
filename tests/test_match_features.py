from datetime import date

from tennis_sabermetrics.features.match_features import (
    MatchFeatureInput,
    PlayerMatchStatLine,
    RankingSnapshot,
    build_match_features_asof,
    orient_match_players,
)


def test_match_features_use_only_prior_rankings_and_matches() -> None:
    rankings = [
        RankingSnapshot(date(2024, 1, 1), "atp", "A", 10, 1000),
        RankingSnapshot(date(2024, 1, 2), "atp", "A", 1, 2000),
        RankingSnapshot(date(2024, 1, 1), "atp", "B", 20, 800),
    ]
    matches = [
        MatchFeatureInput(
            source_key="test",
            tour="atp",
            match_id="m1",
            tournament_id="t1",
            match_date=date(2024, 1, 2),
            surface="Hard",
            round="R32",
            best_of=3,
            tournament_level="A",
            draw_size="32",
            winner_id="A",
            loser_id="B",
            winner_stats=PlayerMatchStatLine("A", 60, 25, 15),
            loser_stats=PlayerMatchStatLine("B", 50, 15, 10),
        ),
        MatchFeatureInput(
            source_key="test",
            tour="atp",
            match_id="m2",
            tournament_id="t1",
            match_date=date(2024, 1, 2),
            surface="Hard",
            round="R32",
            best_of=3,
            tournament_level="A",
            draw_size="32",
            winner_id="B",
            loser_id="A",
        ),
        MatchFeatureInput(
            source_key="test",
            tour="atp",
            match_id="m3",
            tournament_id="t2",
            match_date=date(2024, 1, 3),
            surface="Hard",
            round="R16",
            best_of=3,
            tournament_level="C",
            draw_size="32",
            winner_id="A",
            loser_id="B",
        ),
    ]

    features = build_match_features_asof(matches, rankings, snapshot_date=date(2024, 1, 3))

    same_day_a = next(feature for feature in features if feature.match_id == "m1")
    same_day_b = next(feature for feature in features if feature.match_id == "m2")
    next_day = next(feature for feature in features if feature.match_id == "m3")

    same_day_a_ranks = {
        same_day_a.player_a_id: same_day_a.player_a_rank,
        same_day_a.player_b_id: same_day_a.player_b_rank,
    }
    same_day_a_rank_dates = {
        same_day_a.player_a_id: same_day_a.player_a_rank_asof_date,
        same_day_a.player_b_id: same_day_a.player_b_rank_asof_date,
    }
    next_day_prior_matches = {
        next_day.player_a_id: next_day.player_a_prior_matches,
        next_day.player_b_id: next_day.player_b_prior_matches,
    }
    next_day_serve = {
        next_day.player_a_id: next_day.player_a_serve_points_won_pct_prior,
        next_day.player_b_id: next_day.player_b_serve_points_won_pct_prior,
    }

    assert same_day_a_ranks["A"] == 10
    assert same_day_a_rank_dates["A"] == date(2024, 1, 1)
    assert same_day_a.player_a_won == (same_day_a.player_a_id == "A")
    assert same_day_a.max_feature_asof_date == date(2024, 1, 1)
    assert same_day_b.player_a_prior_matches == 0
    assert same_day_b.player_b_prior_matches == 0
    assert next_day_prior_matches["A"] == 2
    assert next_day_prior_matches["B"] == 2
    assert next_day_serve["A"] == 40 / 60
    assert next_day.tournament_level == "C"
    assert next_day.draw_size == "32"
    assert next_day.max_feature_asof_date == date(2024, 1, 2)


def test_match_orientation_does_not_depend_on_player_id_sorting() -> None:
    match = MatchFeatureInput(
        source_key="test",
        tour="atp",
        match_id="m5",
        tournament_id="t1",
        match_date=date(2024, 1, 2),
        surface="Hard",
        round="R32",
        best_of=3,
        tournament_level="A",
        draw_size="32",
        winner_id="Z",
        loser_id="A",
    )

    player_a_id, player_b_id, player_a_won = orient_match_players(match)

    assert player_a_id == "Z"
    assert player_b_id == "A"
    assert player_a_won is True
