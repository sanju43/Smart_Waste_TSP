from algorithms.nearest_neighbor import nearest_neighbor
from algorithms.two_opt import two_opt
from algorithms.exact_tsp import exact_tsp
from algorithms.validators import validate_locations, validate_route
from services.distance_service import build_distance_matrix
from services.result_service import route_metrics, compare
from math import hypot
from types import SimpleNamespace
import pytest

def matrix(coords):
    return {i: {j: hypot(coords[i][0]-coords[j][0], coords[i][1]-coords[j][1]) for j in coords} for i in coords}

def loc(i, typ, x, y, active=True):
    return SimpleNamespace(id=i, type=typ, x=x, y=y, is_active=active, name=f"L{i}")

def test_distance_matrix_is_symmetric():
    m = matrix({0:(0,0),1:(3,4),2:(3,0)})
    assert m[0][1] == m[1][0] == 5
    assert m[0][2] == m[2][0] == 3

def test_nn_starts_and_ends_at_depot():
    m = matrix({0:(0,0),1:(1,0),2:(1,1),3:(0,1)})
    r = nearest_neighbor([0,1,2,3], m)
    assert r[0] == 0 and r[-1] == 0
    assert sorted(r[1:-1]) == [1,2,3]

def test_two_opt_preserves_nodes():
    m = matrix({0:(0,0),1:(1,1),2:(0,1),3:(1,0)})
    r = two_opt([0,1,2,3,0], m)
    assert r[0] == 0 and r[-1] == 0
    assert sorted(r[1:-1]) == [1,2,3]

def test_exact_solver_known_square():
    m = matrix({0:(0,0),1:(1,0),2:(1,1),3:(0,1)})
    r = exact_tsp([0,1,2,3], m)
    assert r[0] == 0 and r[-1] == 0
    assert route_distance(r, m) == pytest.approx(4.0)

def route_distance(route, distance):
    return sum(distance[route[i]][route[i+1]] for i in range(len(route)-1))

def test_route_validation():
    validate_route([0,1,2,3,0], 0, [1,2,3])

def test_route_validation_rejects_duplicate():
    with pytest.raises(ValueError):
        validate_route([0,1,1,2,0], 0, [1,2])

def test_location_validation_requires_one_depot_and_point():
    depot, points = validate_locations([loc(0,"Depot",0,0), loc(1,"Collection",1,1)])
    assert depot.id == 0 and [p.id for p in points] == [1]

def test_location_validation_rejects_missing_depot():
    with pytest.raises(ValueError):
        validate_locations([loc(1,"Collection",1,1)])

def test_location_validation_rejects_no_points():
    with pytest.raises(ValueError):
        validate_locations([loc(0,"Depot",0,0)])

def test_duplicate_coordinates_are_zero_distance():
    m = matrix({0:(0,0),1:(0,0)})
    assert m[0][1] == 0 and m[1][0] == 0

def test_result_metrics():
    m = matrix({0:(0,0),1:(3,4),2:(6,4)})
    route = [0,1,2,0]
    metrics = route_metrics(route, m, average_speed=30)
    expected_distance = m[0][1] + m[1][2] + m[2][0]
    assert metrics["total_distance"] == pytest.approx(expected_distance)
    assert metrics["stops"] == 2
    comparison = compare([0,2,1,0], route, m)
    assert comparison["improved"] <= comparison["baseline"]
