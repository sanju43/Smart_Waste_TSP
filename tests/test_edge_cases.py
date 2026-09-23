import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from algorithms.validators import find_duplicate_coordinates, validate_locations, validate_route
from database.models import Base, Location, Project
from services.demo_service import load_demo_scenario, reset_demo_scenario
from services.route_service import save_route


def session_factory():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)()


def loc(session, project, name, typ, x=0, y=0, active=True):
    item = Location(project_id=project.id, name=name, type=typ, x=x, y=y, is_active=active)
    session.add(item)
    session.flush()
    return item


def test_zero_collection_points_block_optimization():
    s = session_factory()
    p = Project(name="Zero")
    s.add(p); s.flush()
    depot = loc(s, p, "Depot", "Depot")
    with pytest.raises(ValueError, match="at least one active collection"):
        validate_locations([depot])
    s.close()


def test_one_collection_point_is_valid():
    s = session_factory()
    p = Project(name="One")
    s.add(p); s.flush()
    depot = loc(s, p, "Depot", "Depot", 0, 0)
    point = loc(s, p, "Point", "Collection", 3, 4)
    d = {depot.id: {depot.id: 0, point.id: 5}, point.id: {depot.id: 5, point.id: 0}}
    route = [depot.id, point.id, depot.id]
    assert validate_route(route, depot.id, [point.id])
    assert save_route(s, p.id, route, "Test", d, average_speed=30).total_distance == 10
    s.close()


def test_no_depot_is_blocked():
    s = session_factory()
    p = Project(name="No depot")
    s.add(p); s.flush()
    point = loc(s, p, "Point", "Collection", 1, 1)
    with pytest.raises(ValueError, match="Exactly one active depot"):
        validate_locations([point])
    s.close()


def test_duplicate_coordinates_are_detected_without_blocking_zero_distance():
    s = session_factory()
    p = Project(name="Duplicates")
    s.add(p); s.flush()
    a = loc(s, p, "A", "Collection", 1, 1)
    b = loc(s, p, "B", "Collection", 1, 1)
    groups = find_duplicate_coordinates([a, b])
    assert len(groups) == 1
    assert {x.name for x in groups[0]} == {"A", "B"}
    s.close()


def test_inactive_deleted_point_is_ignored_by_validation():
    s = session_factory()
    p = Project(name="Delete")
    s.add(p); s.flush()
    depot = loc(s, p, "Depot", "Depot", 0, 0)
    active = loc(s, p, "Active", "Collection", 1, 1)
    deleted = loc(s, p, "Deleted", "Collection", 2, 2, active=False)
    d = {depot.id: {depot.id: 0, active.id: 2}, active.id: {depot.id: 2, active.id: 0}}
    route = [depot.id, active.id, depot.id]
    assert validate_locations([depot, active, deleted])[1] == [active]
    assert validate_route(route, depot.id, [active.id])
    s.close()


def test_reset_demo_restores_default_locations():
    s = session_factory()
    project = load_demo_scenario(s, reset=True)
    original_count = s.query(Location).filter_by(project_id=project.id, is_active=True).count()
    extra = Location(project_id=project.id, name="Extra", type="Collection", x=99, y=99)
    s.add(extra); s.commit()
    reset_demo_scenario(s)
    names = {x.name for x in s.query(Location).filter_by(project_id=project.id, is_active=True)}
    assert "Extra" not in names
    assert len(names) == original_count
    s.close()


def test_save_route_rejects_too_short_route():
    s = session_factory()
    p = Project(name="Short")
    s.add(p); s.flush()
    with pytest.raises(ValueError, match="requires a depot"):
        save_route(s, p.id, [1, 1], "Test", {1: {1: 0}}, 30)
    s.close()



def test_full_exhibition_acceptance_flow():
    from services.acceptance_service import run_full_acceptance
    s = session_factory()
    try:
        checks = run_full_acceptance(s)
        assert checks
        assert all(check.status == "PASS" for check in checks), [
            (check.label, check.message) for check in checks if check.status != "PASS"
        ]
        assert {check.key for check in checks} >= {
            "demo_flow", "distance_matrix", "heuristic", "exact", "persistence",
            "animation", "presentation", "export", "results",
        }
    finally:
        s.close()
