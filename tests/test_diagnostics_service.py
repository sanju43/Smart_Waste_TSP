from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, DemoDataset, DistanceMatrix, Location, Project, Route, RoutePoint
from services.diagnostics_service import check_demo_data, check_matrices_and_routes, check_scenarios


def make_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)()


def add_project(session):
    project = Project(name="Demo")
    session.add(project)
    session.flush()
    return project


def add_location(session, project, id_name, typ, x, y):
    item = Location(project_id=project.id, name=id_name, type=typ, x=x, y=y)
    session.add(item)
    session.flush()
    return item


def test_demo_dataset_missing_is_reported():
    session = make_session()
    result = check_demo_data(session)
    assert result.status == "FAIL"
    session.close()


def test_scenario_integrity_requires_one_depot_and_collection():
    session = make_session()
    project = add_project(session)
    add_location(session, project, "Only Point", "Collection", 1, 1)
    result = check_scenarios(session)
    assert result.status == "FAIL"
    session.close()


def test_valid_scenario_passes():
    session = make_session()
    project = add_project(session)
    depot = add_location(session, project, "Depot", "Depot", 0, 0)
    add_location(session, project, "Point", "Collection", 1, 1)
    result = check_scenarios(session)
    assert result.status == "PASS"
    session.close()


def test_incomplete_matrix_is_reported():
    session = make_session()
    project = add_project(session)
    depot = add_location(session, project, "Depot", "Depot", 0, 0)
    point = add_location(session, project, "Point", "Collection", 1, 1)
    session.add(DistanceMatrix(project_id=project.id, from_location_id=depot.id, to_location_id=point.id, distance=1))
    session.commit()
    result = check_matrices_and_routes(session)
    assert result.status == "FAIL"
    session.close()


def test_invalid_completed_route_is_reported():
    session = make_session()
    project = add_project(session)
    depot = add_location(session, project, "Depot", "Depot", 0, 0)
    point = add_location(session, project, "Point", "Collection", 1, 1)
    route = Route(
        project_id=project.id,
        algorithm="Test",
        start_location_id=depot.id,
        total_distance=2,
        estimated_minutes=4,
        total_stops=1,
        status="completed",
    )
    session.add(route)
    session.flush()
    session.add_all([
        RoutePoint(route_id=route.id, location_id=depot.id, sequence_no=1),
        RoutePoint(route_id=route.id, location_id=depot.id, sequence_no=2),
    ])
    session.commit()
    result = check_matrices_and_routes(session)
    assert result.status == "FAIL"
    session.close()
