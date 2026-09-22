from database.database import Base, engine, get_session
from database.models import Location, Project
from services.demo_service import get_average_speed, load_demo_scenario, set_average_speed


def test_demo_load_is_deterministic():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session = get_session()
    try:
        project = load_demo_scenario(session)
        locations = session.query(Location).filter_by(project_id=project.id).order_by(Location.id).all()
        assert len(locations) == 7
        assert sum(x.type == "Depot" for x in locations) == 1
        assert len([x for x in locations if x.type == "Collection"]) == 6
    finally:
        session.close()


def test_average_speed_setting_round_trip():
    session = get_session()
    try:
        set_average_speed(session, 42)
        assert get_average_speed(session) == 42.0
    finally:
        session.close()
