import json

import streamlit as st

from database.database import get_session
from database.models import Location, Project
from services.demo_service import get_average_speed
from services.distance_service import build_distance_matrix
from services.report_service import (
    build_scenario_payload,
    dumps_scenario,
    import_scenario,
    pdf_report_available,
    result_summary_html,
    result_summary_pdf,
    route_csv,
    validate_scenario_payload,
)
from services.result_service import compare, route_metrics, route_rows
from services.route_service import latest_route, load_distance_matrix


st.set_page_config(page_title="Reports & Export", page_icon="📄", layout="wide")
st.title("Reports & Export")
st.caption("Offline-first exports for the current scenario and saved route.")

session = get_session()
try:
    scenario_id = st.session_state.get("scenario_id")
    if not scenario_id:
        st.info("Start a demo or select a scenario before using Reports & Export.")
        st.stop()

    project = session.get(Project, scenario_id)
    if project is None:
        st.error("The selected scenario no longer exists.")
        st.stop()

    locations = (
        session.query(Location)
        .filter_by(project_id=scenario_id, is_active=True)
        .order_by(Location.id)
        .all()
    )
    saved_route = latest_route(session, scenario_id)
    route = st.session_state.get("route")

    if not route and saved_route:
        route = [
            point.location_id
            for point in sorted(saved_route.points, key=lambda item: item.sequence_no)
        ]

    if not locations:
        st.info("The selected scenario has no active locations.")
        st.stop()

    matrix = load_distance_matrix(session, scenario_id)
    if not matrix:
        matrix = build_distance_matrix(locations)

    depot = next((item for item in locations if item.type == "Depot"), None)
    points = [item for item in locations if item.type == "Collection"]
    if not depot or not points:
        st.error("Reports require one depot and at least one collection point.")
        st.stop()

    baseline = [depot.id] + [item.id for item in points] + [depot.id]
    speed = get_average_speed(session)

    if route:
        metrics = route_metrics(route, matrix, average_speed=speed)
        comparison = compare(baseline, route, matrix, average_speed=speed)
        rows = route_rows(route, locations, matrix)
        algorithm = st.session_state.get(
            "algorithm",
            saved_route.algorithm if saved_route else "Current route",
        )
    else:
        metrics = route_metrics(baseline, matrix, average_speed=speed)
        comparison = compare(baseline, baseline, matrix, average_speed=speed)
        rows = route_rows(baseline, locations, matrix)
        algorithm = "Baseline input order"

    st.subheader(f"📦 {project.name}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Distance", f"{metrics['total_distance']:.2f}")
    c2.metric("Distance saved", f"{comparison['saved']:.2f}")
    c3.metric("Stops", metrics["stops"])
    c4.metric("Estimated time", f"{metrics['estimated_minutes']:.1f} min")

    st.subheader("Route CSV")
    st.download_button(
        "⬇ Download route CSV",
        data=route_csv(rows),
        file_name="smart_waste_route.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.subheader("Scenario JSON")
    payload = build_scenario_payload(
        project,
        locations,
        saved_route if route and saved_route else None,
        matrix,
        average_speed=speed,
    )
    json_bytes = dumps_scenario(payload).encode("utf-8")
    st.download_button(
        "⬇ Download scenario JSON",
        data=json_bytes,
        file_name="smart_waste_scenario.json",
        mime="application/json",
        use_container_width=True,
    )

    st.divider()
    st.subheader("Import scenario JSON")
    uploaded = st.file_uploader(
        "Choose a Smart Waste TSP JSON export",
        type=["json"],
        help="Imports the scenario as a new SQLite project; the original scenario is not overwritten.",
    )
    if uploaded is not None and st.button("Import scenario", type="primary"):
        try:
            imported_payload = json.loads(uploaded.getvalue().decode("utf-8"))
            validate_scenario_payload(imported_payload)
            imported = import_scenario(session, imported_payload)
            for key in ("route", "baseline", "metrics", "comparison", "algorithm", "locations", "route_id"):
                st.session_state.pop(key, None)
            st.session_state["scenario_id"] = imported.id
            st.success(f"Imported “{imported.name}” as a new scenario.")
            st.rerun()
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
            session.rollback()
            st.error(f"Import failed: {exc}")

    st.divider()
    st.subheader("Printable result summary")
    html_report = result_summary_html(
        project.name,
        algorithm,
        metrics,
        comparison,
        rows,
        speed,
    )
    st.download_button(
        "⬇ Download printable HTML",
        data=html_report.encode("utf-8"),
        file_name="smart_waste_result_summary.html",
        mime="text/html",
        use_container_width=True,
    )
    st.caption("Open the HTML file locally and use the browser Print command → Save as PDF. No internet is required.")

    st.subheader("Optional PDF exhibition report")
    if pdf_report_available():
        try:
            pdf_bytes = result_summary_pdf(
                project.name,
                algorithm,
                metrics,
                comparison,
                rows,
                speed,
            )
            st.download_button(
                "⬇ Download PDF report",
                data=pdf_bytes,
                file_name="smart_waste_exhibition_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except RuntimeError as exc:
            st.warning(str(exc))
    else:
        st.info(
            "PDF generation is intentionally optional so the core offline exhibition app has no extra PDF dependency. "
            "Use the printable HTML export and browser “Save as PDF”, or install ReportLab separately when a native PDF is required."
        )

    st.divider()
    st.subheader("Route sequence")
    st.dataframe(rows, use_container_width=True, hide_index=True)
finally:
    session.close()
