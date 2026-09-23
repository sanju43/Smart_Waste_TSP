from __future__ import annotations

from dataclasses import dataclass

from algorithms.validators import validate_locations, validate_route
from components.simulation import route_animation_figure
from database.models import Location
from services.demo_service import get_average_speed, load_demo_scenario
from services.distance_service import build_distance_matrix
from services.presentation_service import get_presentation_steps
from services.report_service import (
    build_scenario_payload,
    dumps_scenario,
    import_scenario,
    validate_scenario_payload,
)
from services.result_service import compare, route_metrics
from services.route_service import (
    latest_route,
    load_distance_matrix,
    save_distance_matrix,
    save_route,
)
from services.route_simulation import animation_steps
from services.tsp_optimizer import optimize


@dataclass(frozen=True)
class AcceptanceCheck:
    key: str
    label: str
    status: str
    message: str


def _pass(key, label, message):
    return AcceptanceCheck(key, label, "PASS", message)


def _fail(key, label, exc):
    return AcceptanceCheck(key, label, "FAIL", str(exc))


def run_full_acceptance(session):
    """Exercise the complete offline exhibition flow against the real SQLite session."""
    checks = []
    project = None
    locations = []
    matrix = {}
    route = None
    saved_route = None

    try:
        project = load_demo_scenario(session, reset=True)
        locations = (
            session.query(Location)
            .filter_by(project_id=project.id, is_active=True)
            .order_by(Location.id)
            .all()
        )
        depot, points = validate_locations(locations)
        checks.append(_pass(
            "demo_flow",
            "Start Demo / dataset",
            f"Loaded {len(points)} collection points and exactly one depot.",
        ))
    except Exception as exc:
        return [_fail("demo_flow", "Start Demo / dataset", exc)]

    try:
        matrix = build_distance_matrix(locations)
        save_distance_matrix(session, project.id, locations, matrix)
        stored = load_distance_matrix(session, project.id)
        expected = len(locations) ** 2
        actual = sum(len(row) for row in stored.values())
        if actual != expected:
            raise ValueError(f"Expected {expected} matrix entries, found {actual}.")
        for source in stored:
            for target in stored[source]:
                if abs(stored[source][target] - stored[target][source]) > 1e-9:
                    raise ValueError(f"Matrix is asymmetric for {source} ↔ {target}.")
        checks.append(_pass(
            "distance_matrix",
            "Distance matrix",
            f"Saved and reloaded {actual} pairwise distances; matrix is symmetric.",
        ))
    except Exception as exc:
        checks.append(_fail("distance_matrix", "Distance matrix", exc))
        return checks

    speed = get_average_speed(session)
    ids = [depot.id] + [point.id for point in points]
    baseline = ids + [ids[0]]

    for mode in ("Nearest Neighbor + 2-opt", "Exact (small N)"):
        key = "heuristic" if mode.startswith("Nearest") else "exact"
        try:
            route, algorithm = optimize(ids, matrix, mode)
            validate_route(route, depot.id, [point.id for point in points])
            metrics = route_metrics(route, matrix, average_speed=speed)
            comparison = compare(baseline, route, matrix, average_speed=speed)
            if metrics["total_distance"] < 0:
                raise ValueError("Route distance cannot be negative.")
            saved_route = save_route(
                session,
                project.id,
                route,
                algorithm,
                matrix,
                average_speed=speed,
            )
            checks.append(_pass(
                key,
                f"{mode} optimization",
                f"Valid route saved as Route #{saved_route.id}; "
                f"distance {metrics['total_distance']:.2f}, "
                f"saved {comparison['saved']:.2f}.",
            ))
        except Exception as exc:
            checks.append(_fail(key, f"{mode} optimization", exc))

    try:
        persisted = latest_route(session, project.id)
        if persisted is None:
            raise ValueError("No completed route was persisted.")
        points = sorted(persisted.points, key=lambda item: item.sequence_no)
        persisted_ids = [point.location_id for point in points]
        validate_route(persisted_ids, depot.id, [point.id for point in locations if point.type == "Collection"])
        if abs(float(persisted.total_distance) - route_metrics(persisted_ids, matrix, speed)["total_distance"]) > 1e-9:
            raise ValueError("Persisted route distance does not match the matrix.")
        checks.append(_pass(
            "persistence",
            "SQLite route persistence",
            f"Route #{persisted.id} reloads correctly after save.",
        ))
    except Exception as exc:
        checks.append(_fail("persistence", "SQLite route persistence", exc))

    try:
        frames = animation_steps(locations, route)
        figure = route_animation_figure(locations, route)
        if len(frames) != len(route) or len(figure.frames) != len(route):
            raise ValueError("Animation frame count does not match the route.")
        if frames[-1]["location_id"] != depot.id:
            raise ValueError("Animation does not finish at the depot.")
        checks.append(_pass(
            "animation",
            "Route animation",
            f"Generated {len(frames)} deterministic Plotly animation frames.",
        ))
    except Exception as exc:
        checks.append(_fail("animation", "Route animation", exc))

    try:
        steps = get_presentation_steps()
        if len(steps) < 5 or any(not step.get("title") or not step.get("body") for step in steps):
            raise ValueError("Presentation steps are incomplete.")
        checks.append(_pass(
            "presentation",
            "Presentation mode content",
            f"Validated {len(steps)} guided exhibition steps.",
        ))
    except Exception as exc:
        checks.append(_fail("presentation", "Presentation mode content", exc))

    try:
        payload = build_scenario_payload(
            project,
            locations,
            saved_route,
            matrix,
            average_speed=speed,
        )
        validate_scenario_payload(payload)
        serialized = dumps_scenario(payload)
        if "distance_matrix" not in payload or not payload["distance_matrix"]:
            raise ValueError("Scenario export omitted the distance matrix.")
        if not serialized.strip().startswith("{"):
            raise ValueError("Scenario export is not valid JSON text.")
        checks.append(_pass(
            "export",
            "Scenario export",
            f"Validated versioned JSON export with {len(payload['locations'])} locations.",
        ))
    except Exception as exc:
        checks.append(_fail("export", "Scenario export", exc))

    try:
        imported_payload = validate_scenario_payload(payload)
        imported = import_scenario(session, imported_payload, name_override="Acceptance Import")
        imported_locations = (
            session.query(Location)
            .filter_by(project_id=imported.id, is_active=True)
            .order_by(Location.id)
            .all()
        )
        if len(imported_locations) != len(locations):
            raise ValueError(
                f"Imported scenario has {len(imported_locations)} locations; expected {len(locations)}."
            )
        imported_route = latest_route(session, imported.id)
        if imported_route is None:
            raise ValueError("Imported scenario did not restore the saved route.")
        imported_matrix = load_distance_matrix(session, imported.id)
        if not imported_matrix:
            raise ValueError("Imported scenario did not restore the distance matrix.")
        imported_ids = [
            point.location_id
            for point in sorted(imported_route.points, key=lambda item: item.sequence_no)
        ]
        imported_depot, imported_points = validate_locations(imported_locations)
        validate_route(imported_ids, imported_depot.id, [point.id for point in imported_points])
        checks.append(_pass(
            "import",
            "Scenario import round-trip",
            f"Imported scenario #{imported.id} with {len(imported_locations)} locations and a valid saved route.",
        ))
    except Exception as exc:
        checks.append(_fail("import", "Scenario import round-trip", exc))

    try:
        route = [
            point.location_id
            for point in sorted(saved_route.points, key=lambda item: item.sequence_no)
        ]
        metrics = route_metrics(route, matrix, average_speed=speed)
        comparison = compare(baseline, route, matrix, average_speed=speed)
        if abs(comparison["improved"] - metrics["total_distance"]) > 1e-9:
            raise ValueError("Results comparison does not match route metrics.")
        if abs(comparison["improved"] / speed * 60 - metrics["estimated_minutes"]) > 1e-9:
            raise ValueError("Estimated time does not match configured average speed.")
        checks.append(_pass(
            "results",
            "Results & comparison",
            f"Distance/time metrics are internally consistent at {speed:g} km/h.",
        ))
    except Exception as exc:
        checks.append(_fail("results", "Results & comparison", exc))

    return checks
