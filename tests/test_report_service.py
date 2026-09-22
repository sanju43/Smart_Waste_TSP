import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Location, Project
from services.report_service import (
    build_scenario_payload,
    dumps_scenario,
    import_scenario,
    result_summary_html,
    route_csv,
    validate_scenario_payload,
)


class LocationStub:
    def __init__(self, id, name, type, x=0, y=0):
        self.id = id
        self.name = name
        self.type = type
        self.x = x
        self.y = y
        self.latitude = None
        self.longitude = None
        self.waste_kg = 10
        self.priority = 1
        self.is_active = True


def test_route_csv_has_header_and_all_rows():
    rows = [
        {"Stop": 1, "Location": "Depot", "Type": "Depot", "Distance from previous": 0, "Cumulative distance": 0},
        {"Stop": 2, "Location": "School", "Type": "Collection", "Distance from previous": 3.5, "Cumulative distance": 3.5},
    ]
    csv_text = route_csv(rows)
    assert csv_text.startswith("Stop,Location,Type,Distance from previous,Cumulative distance")
    assert "School" in csv_text
    assert "3.5" in csv_text


def test_scenario_json_round_trip_shape():
    project = Project(name="Demo", description="Offline")
    locations = [LocationStub(1, "Depot", "Depot"), LocationStub(2, "School", "Collection")]
    payload = build_scenario_payload(
        project,
        locations,
        matrix={1: {1: 0, 2: 3}, 2: {1: 3, 2: 0}},
        average_speed=30,
    )
    restored = json.loads(dumps_scenario(payload))
    validate_scenario_payload(restored)
    assert restored["schema_version"] == 1
    assert restored["project"]["name"] == "Demo"
    assert len(restored["locations"]) == 2


def test_import_scenario_creates_new_project_and_remaps_ids():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True)()

    payload = {
        "schema_version": 1,
        "project": {"name": "Imported Demo", "description": "Copy"},
        "settings": {"average_speed_kmh": 30},
        "locations": [
            {"id": 101, "name": "Depot", "type": "Depot", "x": 0, "y": 0, "latitude": None, "longitude": None, "waste_kg": 0, "priority": 1, "is_active": True},
            {"id": 102, "name": "School", "type": "Collection", "x": 3, "y": 4, "latitude": None, "longitude": None, "waste_kg": 10, "priority": 2, "is_active": True},
        ],
        "distance_matrix": [
            {"from_location_id": 101, "to_location_id": 101, "distance": 0},
            {"from_location_id": 101, "to_location_id": 102, "distance": 5},
            {"from_location_id": 102, "to_location_id": 101, "distance": 5},
            {"from_location_id": 102, "to_location_id": 102, "distance": 0},
        ],
    }

    imported = import_scenario(session, payload)
    assert imported.id == 1
    assert imported.name == "Imported Demo"
    assert len(imported.locations) == 2
    assert imported.locations[0].project_id == imported.id


def test_printable_report_contains_print_css_and_route():
    html = result_summary_html(
        "Demo",
        "Nearest Neighbor + 2-opt",
        {"estimated_minutes": 10, "stops": 2},
        {
            "baseline": 20,
            "improved": 15,
            "saved": 5,
            "baseline_minutes": 12,
            "improved_minutes": 10,
        },
        [
            {"Stop": 1, "Location": "Depot", "Type": "Depot", "Distance from previous": 0, "Cumulative distance": 0},
            {"Stop": 2, "Location": "School", "Type": "Collection", "Distance from previous": 5, "Cumulative distance": 5},
        ],
        30,
    )
    assert "@media print" in html
    assert "Nearest Neighbor + 2-opt" in html
    assert "School" in html


def test_validate_rejects_duplicate_location_ids():
    payload = {
        "schema_version": 1,
        "project": {"name": "Bad"},
        "locations": [
            {"id": 1, "name": "Depot", "type": "Depot"},
            {"id": 1, "name": "Point", "type": "Collection"},
        ],
    }
    with pytest.raises(ValueError, match="duplicate"):
        validate_scenario_payload(payload)
