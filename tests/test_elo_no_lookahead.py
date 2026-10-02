from datetime import date

from tennis_sabermetrics.models.elo import (
    MatchResult,
    run_blended_surface_elo,
    run_elo,
    run_surface_elo,
)


def test_elo_predicts_before_updating() -> None:
    matches = [
        MatchResult(date(2024, 1, 2), winner_id="A", loser_id="B", order=2),
        MatchResult(date(2024, 1, 1), winner_id="A", loser_id="B", order=1),
    ]

    predictions = run_elo(matches)

    assert predictions[0].match.match_date == date(2024, 1, 1)
    assert predictions[0].winner_pre_rating == 1500.0
    assert predictions[0].loser_pre_rating == 1500.0
    assert predictions[0].winner_probability == 0.5
    assert predictions[1].winner_pre_rating > predictions[1].loser_pre_rating


def test_surface_elo_is_independent_by_surface() -> None:
    matches = [
        MatchResult(date(2024, 1, 1), winner_id="A", loser_id="B", surface="clay", order=1),
        MatchResult(date(2024, 1, 2), winner_id="A", loser_id="B", surface="hard", order=2),
        MatchResult(date(2024, 1, 3), winner_id="A", loser_id="B", surface="clay", order=3),
    ]

    predictions = run_surface_elo(matches)

    assert predictions[0].winner_probability == 0.5
    assert predictions[1].winner_probability == 0.5
    assert predictions[2].winner_pre_rating > predictions[2].loser_pre_rating


def test_blended_surface_elo_shrinks_sparse_surfaces_toward_overall_rating() -> None:
    matches = [
        MatchResult(date(2024, 1, 1), winner_id="A", loser_id="B", surface="clay", order=1),
        MatchResult(date(2024, 1, 2), winner_id="A", loser_id="B", surface="hard", order=2),
        MatchResult(date(2024, 1, 3), winner_id="A", loser_id="B", surface="clay", order=3),
    ]

    predictions = run_blended_surface_elo(matches)

    assert predictions[0].winner_probability == 0.5
    assert predictions[1].winner_probability > 0.5
    assert predictions[2].winner_pre_rating > predictions[2].loser_pre_rating
