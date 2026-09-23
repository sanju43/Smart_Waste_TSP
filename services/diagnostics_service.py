from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import inspect, text

from algorithms.validators import validate_route
from database.models import DemoDataset, DistanceMatrix, Location, Project, Route


@dataclass(frozen=True)
class DiagnosticCheck:
    key: str
    label: str
    status: str
    message: str


REQUIRED_PACKAGES = (
    "streamlit",
    "pandas",
    "numpy",
    "plotly",
    "networkx",
    "sqlalchemy",
    "pytest",
)


def _check(key, label, ok, message, warning=False):
    return DiagnosticCheck(
        key=key,
        label=label,
        status="WARNING" if warning else ("PASS" if ok else "FAIL"),
        message=message,
    )


def check_database(session):
    try:
        session.execute(text("SELECT 1")).scalar_one()
        tables = set(inspect(session.bind).get_table_names())
        required = {
            "projects",
            "locations",
            "routes",
            "route_points",
            "distance_matrix",
            "demo_datasets",
            "settings",
        }
        missing = sorted(required - tables)
        if missing:
            return _check(
                "database",
                "SQLite database",
                False,
                "Missing tables: " + ", ".join(missing),
            )
        return _check("database", "SQLite database", True, "Database connection and required tables are available.")
    except Exception as exc:
        return _check("database", "SQLite database", False, f"Database check failed: {exc}")


def check_dependencies():
    missing = [name for name in REQUIRED_PACKAGES if importlib.util.find_spec(name) is None]
    if missing:
        return _check(
            "dependencies",
            "Core dependencies",
            False,
            "Missing required packages: " + ", ".join(missing),
        )
    return _check(
        "dependencies",
        "Core dependencies",
        True,
        "All fixed-stack runtime/test packages are importable.",
    )


def check_demo_data(session):
    dataset = session.query(DemoDataset).filter_by(name="Exhibition Demo").first()
    if dataset is None:
        return _check("demo_data", "Demo dataset", False, "The Exhibition Demo dataset is missing.")
    try:
        import json

        payload = json.loads(dataset.payload)
        if not isinstance(payload, list) or not payload:
            raise ValueError("dataset payload is empty")
        depot_count = sum(item.get("type") == "Depot" for item in payload if isinstance(item, dict))
        if depot_count != 1:
            return _check("demo_data", "Demo dataset", False, "Exhibition Demo must contain exactly one depot.")
        return _check("demo_data", "Demo dataset", True, f"Exhibition Demo contains {len(payload)} locations.")
    except Exception as exc:
        return _check("demo_data", "Demo dataset", False, f"Demo dataset is invalid: {exc}")


def check_scenarios(session):
    projects = session.query(Project).order_by(Project.id).all()
    if not projects:
        return _check(
            "scenarios",
            "Scenario integrity",
            True,
            "No scenarios exist yet; this is valid before the first demo/scenario is created.",
            warning=True,
        )

    failures = []
    for project in projects:
        locations = (
            session.query(Location)
            .filter_by(project_id=project.id, is_active=True)
            .order_by(Location.id)
            .all()
        )
        depots = [item for item in locations if item.type == "Depot"]
        points = [item for item in locations if item.type == "Collection"]

        if len(depots) != 1:
            failures.append(f"{project.name}: expected 1 active depot, found {len(depots)}")
        if not points:
            failures.append(f"{project.name}: no active collection points")

        for item in locations:
            if not math.isfinite(float(item.x)) or not math.isfinite(float(item.y)):
                failures.append(f"{project.name}: {item.name} has non-finite coordinates")

    if failures:
        return _check("scenarios", "Scenario integrity", False, " | ".join(failures[:5]))
    return _check("scenarios", "Scenario integrity", True, f"Validated {len(projects)} scenario(s).")


def check_matrices_and_routes(session):
    projects = session.query(Project).order_by(Project.id).all()
    warnings = []
    failures = []

    for project in projects:
        locations = (
            session.query(Location)
            .filter_by(project_id=project.id, is_active=True)
            .order_by(Location.id)
            .all()
        )
        ids = {item.id for item in locations}
        matrix_rows = session.query(DistanceMatrix).filter_by(project_id=project.id).all()
        if matrix_rows:
            matrix = {}
            for row in matrix_rows:
                matrix.setdefault(row.from_location_id, {})[row.to_location_id] = float(row.distance)

            missing = [
                (source, target)
                for source in ids
                for target in ids
                if target not in matrix.get(source, {})
            ]
            if missing:
                failures.append(f"{project.name}: distance matrix is incomplete ({len(missing)} missing pairs)")
            else:
                asymmetric = [
                    (a, b)
                    for a in ids
                    for b in ids
                    if abs(matrix[a][b] - matrix[b][a]) > 1e-9
                ]
                if asymmetric:
                    failures.append(f"{project.name}: distance matrix is not symmetric")
        elif locations:
            warnings.append(f"{project.name}: no saved distance matrix; it will be rebuilt when needed")

        for route in (
            session.query(Route)
            .filter_by(project_id=project.id, status="completed")
            .order_by(Route.id)
            .all()
        ):
            points = sorted(route.points, key=lambda point: point.sequence_no)
            route_ids = [point.location_id for point in points]
            depot = next((item for item in locations if item.type == "Depot"), None)
            collection_ids = [item.id for item in locations if item.type == "Collection"]
            if depot is None:
                failures.append(f"{project.name}: completed route #{route.id} has no active depot")
                continue
            try:
                validate_route(route_ids, depot.id, collection_ids)
            except ValueError as exc:
                failures.append(f"{project.name}: route #{route.id} invalid: {exc}")

    if failures:
        return _check("matrices_routes", "Matrix & saved-route integrity", False, " | ".join(failures[:5]))
    if warnings:
        return _check("matrices_routes", "Matrix & saved-route integrity", True, " | ".join(warnings[:5]), warning=True)
    return _check("matrices_routes", "Matrix & saved-route integrity", True, "Saved matrices and completed routes are structurally valid.")


def run_diagnostics(session):
    return [
        check_database(session),
        check_dependencies(),
        check_demo_data(session),
        check_scenarios(session),
        check_matrices_and_routes(session),
    ]


def run_test_suite(project_root: str | Path | None = None, timeout_seconds=60):
    root = Path(project_root or Path(__file__).resolve().parents[1])
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        output = (completed.stdout + "\n" + completed.stderr).strip()
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "output": output[-12000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        output = ((exc.stdout or "") + "\n" + (exc.stderr or "")).strip()
        return {
            "ok": False,
            "returncode": None,
            "output": output[-12000:],
            "timed_out": True,
        }
