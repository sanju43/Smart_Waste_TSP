import pytest

from services.result_service import compare, route_metrics, route_rows


@pytest.fixture
def matrix():
    return {
        1: {1: 0, 2: 3, 3: 4},
        2: {1: 3, 2: 0, 3: 5},
        3: {1: 4, 2: 5, 3: 0},
    }


class LocationStub:
    def __init__(self, id, name, type):
        self.id = id
        self.name = name
        self.type = type


def test_route_metrics_and_speed(matrix):
    result = route_metrics([1, 2, 3, 1], matrix, average_speed=30)
    assert result["total_distance"] == 12
    assert result["estimated_minutes"] == 24
    assert result["stops"] == 2


def test_compare_uses_same_speed_for_both_routes(matrix):
    result = compare([1, 2, 3, 1], [1, 3, 2, 1], matrix, average_speed=60)
    assert result["baseline"] == 12
    assert result["improved"] == 12
    assert result["saved"] == 0
    assert result["percent_saved"] == 0
    assert result["baseline_minutes"] == 12
    assert result["improved_minutes"] == 12


def test_route_rows_include_stop_and_cumulative_distance(matrix):
    locations = [
        LocationStub(1, "Depot", "Depot"),
        LocationStub(2, "School", "Collection"),
        LocationStub(3, "Market", "Collection"),
    ]
    rows = route_rows([1, 2, 3, 1], locations, matrix)
    assert rows[0]["Location"] == "Depot"
    assert rows[1]["Distance from previous"] == 3
    assert rows[-1]["Cumulative distance"] == 12
    assert len(rows) == 4
