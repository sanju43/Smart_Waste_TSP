import csv
import io
import json
from datetime import datetime
from html import escape


REPORT_SCHEMA_VERSION = 1


def _iso(value):
    return value.isoformat() if value else None


def build_scenario_payload(project, locations, route_row=None, matrix=None, average_speed=30.0):
    """Build a JSON-safe, versioned snapshot of a scenario and optional saved route."""
    payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "exported_at": datetime.utcnow().isoformat(),
        "project": {
            "name": project.name,
            "description": project.description,
        },
        "settings": {"average_speed_kmh": float(average_speed)},
        "locations": [
            {
                "id": location.id,
                "name": location.name,
                "type": location.type,
                "x": float(location.x),
                "y": float(location.y),
                "latitude": location.latitude,
                "longitude": location.longitude,
                "waste_kg": float(location.waste_kg or 0),
                "priority": int(location.priority or 1),
                "is_active": bool(location.is_active),
            }
            for location in locations
        ],
    }

    if matrix:
        payload["distance_matrix"] = [
            {
                "from_location_id": int(source),
                "to_location_id": int(target),
                "distance": float(distance),
            }
            for source, targets in matrix.items()
            for target, distance in targets.items()
        ]
    else:
        payload["distance_matrix"] = []

    if route_row:
        points = sorted(route_row.points, key=lambda point: point.sequence_no)
        payload["route"] = {
            "algorithm": route_row.algorithm,
            "start_location_id": int(route_row.start_location_id),
            "total_distance": float(route_row.total_distance),
            "estimated_minutes": float(route_row.estimated_minutes),
            "total_stops": int(route_row.total_stops),
            "status": route_row.status,
            "points": [
                {
                    "location_id": int(point.location_id),
                    "sequence_no": int(point.sequence_no),
                    "distance_from_previous": float(point.distance_from_previous),
                    "cumulative_distance": float(point.cumulative_distance),
                }
                for point in points
            ],
        }

    return payload


def dumps_scenario(payload):
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False)


def validate_scenario_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("Scenario export must be a JSON object.")
    if payload.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported scenario schema version: {payload.get('schema_version')!r}."
        )

    project = payload.get("project")
    locations = payload.get("locations")
    if not isinstance(project, dict) or not project.get("name"):
        raise ValueError("Scenario export must contain project.name.")
    if not isinstance(locations, list):
        raise ValueError("Scenario export must contain a locations list.")

    ids = [item.get("id") for item in locations]
    if any(not isinstance(item, dict) for item in locations):
        raise ValueError("Every exported location must be an object.")
    if len(ids) != len(set(ids)):
        raise ValueError("Export contains duplicate location ids.")

    depots = [item for item in locations if item.get("type") == "Depot" and item.get("is_active", True)]
    if len(depots) > 1:
        raise ValueError("Scenario export contains more than one active depot.")

    route = payload.get("route")
    if route is not None:
        if not isinstance(route, dict) or not isinstance(route.get("points"), list):
            raise ValueError("Exported route must contain a points list.")

    return payload


def import_scenario(session, payload, name_override=None):
    """Import a versioned snapshot as a new scenario and remap database ids."""
    from database.models import DistanceMatrix, Location, Project, Route, RoutePoint

    validate_scenario_payload(payload)

    project_data = payload["project"]
    project_name = name_override.strip() if name_override else project_data["name"]
    project = Project(name=project_name, description=project_data.get("description"))
    session.add(project)
    session.flush()

    id_map = {}
    for item in payload["locations"]:
        location = Location(
            project_id=project.id,
            name=item["name"],
            type=item.get("type", "Collection"),
            x=float(item["x"]),
            y=float(item["y"]),
            latitude=item.get("latitude"),
            longitude=item.get("longitude"),
            waste_kg=float(item.get("waste_kg") or 0),
            priority=int(item.get("priority") or 1),
            is_active=bool(item.get("is_active", True)),
        )
        session.add(location)
        session.flush()
        id_map[int(item["id"])] = location.id

    for item in payload.get("distance_matrix", []):
        source = id_map.get(int(item["from_location_id"]))
        target = id_map.get(int(item["to_location_id"]))
        if source is None or target is None:
            raise ValueError("Distance matrix references an unknown location.")
        session.add(
            DistanceMatrix(
                project_id=project.id,
                from_location_id=source,
                to_location_id=target,
                distance=float(item["distance"]),
            )
        )

    route_data = payload.get("route")
    if route_data:
        start_id = id_map.get(int(route_data["start_location_id"]))
        if start_id is None:
            raise ValueError("Saved route references an unknown start location.")

        route = Route(
            project_id=project.id,
            algorithm=route_data.get("algorithm", "Imported"),
            start_location_id=start_id,
            total_distance=float(route_data.get("total_distance", 0)),
            estimated_minutes=float(route_data.get("estimated_minutes", 0)),
            total_stops=int(route_data.get("total_stops", 0)),
            status="completed",
        )
        session.add(route)
        session.flush()

        for point in route_data["points"]:
            location_id = id_map.get(int(point["location_id"]))
            if location_id is None:
                raise ValueError("Saved route references an unknown location.")
            session.add(
                RoutePoint(
                    route_id=route.id,
                    location_id=location_id,
                    sequence_no=int(point["sequence_no"]),
                    distance_from_previous=float(point.get("distance_from_previous", 0)),
                    cumulative_distance=float(point.get("cumulative_distance", 0)),
                )
            )

    session.commit()
    return project


def route_csv(route_rows):
    """Return a UTF-8 CSV document for a route sequence."""
    output = io.StringIO(newline="")
    fields = [
        "Stop",
        "Location",
        "Type",
        "Distance from previous",
        "Cumulative distance",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(route_rows)
    return output.getvalue()


def result_summary_html(
    project_name,
    algorithm,
    metrics,
    comparison,
    rows,
    average_speed,
):
    """Build a self-contained printable report; no external assets or network calls."""
    route_items = "".join(
        "<tr>"
        f"<td>{row['Stop']}</td>"
        f"<td>{escape(str(row['Location']))}</td>"
        f"<td>{escape(str(row['Type']))}</td>"
        f"<td>{row['Distance from previous']:.2f}</td>"
        f"<td>{row['Cumulative distance']:.2f}</td>"
        "</tr>"
        for row in rows
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{escape(project_name)} - Smart Waste TSP Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2937; }}
h1 {{ margin-bottom: 4px; }}
.subtitle {{ color: #4b5563; margin-bottom: 24px; }}
.grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
.card {{ border: 1px solid #d1d5db; border-radius: 8px; padding: 14px; }}
.card strong {{ display: block; font-size: 20px; margin-top: 4px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; }}
th {{ background: #f3f4f6; }}
.note {{ margin-top: 18px; color: #4b5563; }}
@media print {{
  body {{ margin: 12mm; }}
  .no-print {{ display: none; }}
  .card {{ break-inside: avoid; }}
}}
</style>
</head>
<body>
<h1>Smart Waste Collection Route Optimizer</h1>
<div class="subtitle">{escape(project_name)} · Results &amp; Comparison</div>
<div class="grid">
<div class="card">Baseline distance<strong>{comparison["baseline"]:.2f}</strong></div>
<div class="card">Improved distance<strong>{comparison["improved"]:.2f}</strong></div>
<div class="card">Distance saved<strong>{comparison["saved"]:.2f}</strong></div>
<div class="card">Estimated time<strong>{metrics["estimated_minutes"]:.1f} min</strong></div>
</div>
<p><strong>Algorithm:</strong> {escape(str(algorithm))}<br>
<strong>Average speed:</strong> {float(average_speed):g} km/h<br>
<strong>Collection stops:</strong> {metrics["stops"]}<br>
<strong>Baseline time:</strong> {comparison["baseline_minutes"]:.1f} min ·
<strong>Improved time:</strong> {comparison["improved_minutes"]:.1f} min ·
<strong>Time saved:</strong> {comparison["baseline_minutes"] - comparison["improved_minutes"]:.1f} min</p>
<table>
<thead><tr><th>Stop</th><th>Location</th><th>Type</th><th>Distance from previous</th><th>Cumulative distance</th></tr></thead>
<tbody>{route_items}</tbody>
</table>
<p class="note">This report uses the project's offline coordinate-grid distance model and saved route results.</p>
<p class="no-print">Print this page from the browser and choose “Save as PDF” for a PDF copy.</p>
</body>
</html>"""


def pdf_report_available():
    try:
        import reportlab  # noqa: F401
    except ImportError:
        return False
    return True


def result_summary_pdf(project_name, algorithm, metrics, comparison, rows, average_speed):
    """Return PDF bytes when optional ReportLab is installed; core app does not require it."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    except ImportError as exc:
        raise RuntimeError(
            "PDF export is optional. Install ReportLab only when PDF generation is needed."
        ) from exc

    output = io.BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Smart Waste Collection Route Optimizer", styles["Title"]),
        Paragraph(f"{escape(project_name)} · Results & Comparison", styles["Heading2"]),
        Spacer(1, 12),
        Paragraph(
            f"Algorithm: {escape(str(algorithm))}<br/>"
            f"Baseline distance: {comparison['baseline']:.2f}<br/>"
            f"Improved distance: {comparison['improved']:.2f}<br/>"
            f"Distance saved: {comparison['saved']:.2f}<br/>"
            f"Estimated time: {metrics['estimated_minutes']:.1f} min<br/>"
            f"Average speed: {float(average_speed):g} km/h<br/>"
            f"Collection stops: {metrics['stops']}",
            styles["BodyText"],
        ),
        Spacer(1, 12),
    ]

    table_data = [["Stop", "Location", "Type", "Leg distance", "Cumulative"]]
    table_data.extend(
        [
            str(row["Stop"]),
            str(row["Location"]),
            str(row["Type"]),
            f"{row['Distance from previous']:.2f}",
            f"{row['Cumulative distance']:.2f}",
        ]
        for row in rows
    )
    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)
    document.build(story)
    return output.getvalue()
