import json

from database.models import DemoDataset, Location, Project, Setting

DEMO_NAME = "Exhibition Demo"
DEFAULT_AVERAGE_SPEED_KMH = 30.0
DEMO_LOCATIONS = [
    {"name": "D0 - Depot", "type": "Depot", "x": 10.0, "y": 10.0, "waste_kg": 0.0, "priority": 1},
    {"name": "P1 - School", "type": "Collection", "x": 20.0, "y": 15.0, "waste_kg": 50.0, "priority": 2},
    {"name": "P2 - Market", "type": "Collection", "x": 35.0, "y": 12.0, "waste_kg": 80.0, "priority": 3},
    {"name": "P3 - Society A", "type": "Collection", "x": 45.0, "y": 30.0, "waste_kg": 60.0, "priority": 2},
    {"name": "P4 - Hospital", "type": "Collection", "x": 30.0, "y": 40.0, "waste_kg": 40.0, "priority": 3},
    {"name": "P5 - Park", "type": "Collection", "x": 15.0, "y": 35.0, "waste_kg": 30.0, "priority": 1},
    {"name": "P6 - Society B", "type": "Collection", "x": 50.0, "y": 45.0, "waste_kg": 70.0, "priority": 2},
]


def _ensure_dataset(session):
    dataset = session.query(DemoDataset).filter_by(name=DEMO_NAME).first()
    if not dataset:
        dataset = DemoDataset(name=DEMO_NAME, payload=json.dumps(DEMO_LOCATIONS))
        session.add(dataset)
        session.flush()
    return dataset


def get_setting(session, key, default=None):
    row = session.query(Setting).filter_by(key=key).first()
    return row.value if row else default


def get_average_speed(session):
    raw = get_setting(session, "average_speed_kmh", str(DEFAULT_AVERAGE_SPEED_KMH))
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return DEFAULT_AVERAGE_SPEED_KMH
    return value if value > 0 else DEFAULT_AVERAGE_SPEED_KMH


def set_average_speed(session, speed_kmh):
    speed = float(speed_kmh)
    if speed <= 0:
        raise ValueError("Average vehicle speed must be greater than zero.")
    row = session.query(Setting).filter_by(key="average_speed_kmh").first()
    if row:
        row.value = str(speed)
    else:
        session.add(Setting(key="average_speed_kmh", value=str(speed)))
    session.commit()
    return speed


def load_demo_scenario(session, reset=True):
    dataset = _ensure_dataset(session)
    project = session.query(Project).filter_by(name=DEMO_NAME).first()
    if not project:
        project = Project(name=DEMO_NAME, description="Deterministic offline exhibition dataset")
        session.add(project)
        session.flush()

    if reset:
        session.query(Location).filter_by(project_id=project.id).delete()
        for route in project.routes:
            route.status = "invalidated"
        for matrix in list(project.distance_matrices):
            session.delete(matrix)
        session.flush()

    payload = json.loads(dataset.payload)
    if not isinstance(payload, list) or not payload:
        raise ValueError("Exhibition Demo dataset is empty or invalid.")

    for item in payload:
        if item.get("type") not in {"Depot", "Collection"}:
            raise ValueError("Exhibition Demo contains an invalid location type.")
        session.add(Location(project_id=project.id, **item))

    session.commit()
    return project


def reset_demo_scenario(session):
    return load_demo_scenario(session, reset=True)
