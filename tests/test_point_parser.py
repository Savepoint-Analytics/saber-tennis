from tennis_sabermetrics.transform.parse_points import parse_point_sequence


def test_parse_point_sequence_with_game_and_set_separators() -> None:
    points = parse_point_sequence("SSRD;ADRS.RS")

    assert len(points) == 10
    assert points[0].set_index == 0
    assert points[4].game_index == 1
    assert points[-1].set_index == 1
    assert points[4].is_ace
    assert points[5].is_double_fault


def test_tiebreak_serve_change_marker_is_ignored() -> None:
    points = parse_point_sequence("SR/RS")

    assert [point.code for point in points] == ["S", "R", "R", "S"]

