import pytest

from tennis_sabermetrics.transform.parse_scores import parse_match_score


def test_parse_straight_sets_with_tiebreak() -> None:
    score = parse_match_score("6-4 7-6(5)")

    assert score.status == "completed"
    assert len(score.sets) == 2
    assert score.sets[1].went_to_tiebreak
    assert score.sets[1].tiebreak_loser_points == 5


def test_parse_best_of_five() -> None:
    score = parse_match_score("6-4 3-6 7-6(4) 2-6 6-3")

    assert score.best_of == 5
    assert len(score.sets) == 5


def test_parse_retirement_status() -> None:
    score = parse_match_score("6-4 2-1 RET")

    assert score.status == "retirement"


def test_parse_walkover_without_sets() -> None:
    score = parse_match_score("W/O")

    assert score.status == "walkover"
    assert score.sets == ()


def test_parse_match_tiebreak_and_full_tiebreak_score() -> None:
    score = parse_match_score("6-4 3-6 [10-8]")
    full_tiebreak = parse_match_score("7-6(10-8)")

    assert score.sets[-1].is_match_tiebreak
    assert full_tiebreak.sets[0].tiebreak_winner_points == 10
    assert full_tiebreak.sets[0].tiebreak_loser_points == 8


def test_invalid_score_raises() -> None:
    with pytest.raises(ValueError):
        parse_match_score("six-four")
