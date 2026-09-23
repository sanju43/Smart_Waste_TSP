import streamlit as st

from components.metric_cards import show_metrics
from components.route_chart import comparison_chart
from components.simulation import route_animation_figure
from database.database import get_session
from database.models import Location
from services.demo_service import get_average_speed
from services.distance_service import build_distance_matrix
from services.result_service import compare, route_metrics, route_rows
from services.route_service import latest_route, load_distance_matrix

st.title("Results & Comparison")
st.caption("Baseline vs improved route, persisted route metrics, and stop-by-stop sequence.")

session = get_session()
try:
    scenario_id = st.session_state.get("scenario_id")
    route = st.session_state.get("route")

    if scenario_id:
        locations = (
            session.query(Location)
            .filter_by(project_id=scenario_id, is_active=True)
            .order_by(Location.id)
            .all()
        )

    if not scenario_id or not locations:
        st.info("Start a demo or create a scenario, then optimize a route.")
        st.stop()

    saved_route = latest_route(session, scenario_id)
    if not route and saved_route:
        route = [
            point.location_id
            for point in sorted(saved_route.points, key=lambda item: item.sequence_no)
        ]
        st.session_state["route"] = route
        st.session_state["route_id"] = saved_route.id

    if not route:
        st.info("Run the optimizer first.")
        st.stop()

    matrix = load_distance_matrix(session, scenario_id)
    if not matrix:
        matrix = build_distance_matrix(locations)

    baseline = st.session_state.get("baseline")
    if not baseline:
        depot = next((item for item in locations if item.type == "Depot"), None)
        points = [item for item in locations if item.type == "Collection"]
        if not depot or not points:
            st.error("Results require exactly one depot and at least one collection point.")
            st.stop()
        baseline = [depot.id] + [item.id for item in points] + [depot.id]
        st.session_state["baseline"] = baseline

    speed = get_average_speed(session)
    metrics = route_metrics(route, matrix, average_speed=speed)
    comparison = compare(baseline, route, matrix, average_speed=speed)
    st.session_state.update({"metrics": metrics, "comparison": comparison})

    show_metrics(metrics, comparison)

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Baseline distance", f"{comparison['baseline']:.2f}")
        st.caption(f"Estimated baseline time: {comparison['baseline_minutes']:.1f} min")
    with c2:
        st.metric("Improved distance", f"{comparison['improved']:.2f}")
        st.caption(f"Estimated improved time: {comparison['improved_minutes']:.1f} min")

    st.plotly_chart(
        comparison_chart(comparison["baseline"], comparison["improved"]),
        use_container_width=True,
    )

    st.subheader("Route sequence")
    st.dataframe(
        route_rows(route, locations, matrix),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        f"Algorithm: {st.session_state.get('algorithm', saved_route.algorithm if saved_route else 'Saved route')} "
        f"· Average speed: {speed:g} km/h"
    )

    st.divider()
    st.subheader("🚛 Route Simulation")
    st.caption("Use the Plotly controls to play, pause, or inspect each stop.")
    st.plotly_chart(
        route_animation_figure(locations, route),
        use_container_width=True,
    )
finally:
    session.close()
