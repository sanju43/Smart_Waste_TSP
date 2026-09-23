import streamlit as st

from algorithms.validators import validate_locations, validate_route
from components.map_view import route_figure
from database.database import get_session
from database.models import Location
from services.demo_service import get_average_speed, load_demo_scenario, set_average_speed
from services.distance_service import build_distance_matrix
from services.result_service import compare, route_metrics
from services.route_service import save_distance_matrix, save_route
from services.tsp_optimizer import optimize

st.title("Dashboard")
st.caption("Offline-first exhibition control panel")

s = get_session()
try:
    speed = get_average_speed(s)
    st.subheader("Exhibition Demo")
    st.write("Load the deterministic seven-point demo, optimize it, and prepare the result for the Results and Science pages.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("▶ Start Demo", type="primary", use_container_width=True):
            project = load_demo_scenario(s, reset=True)
            loc = s.query(Location).filter_by(project_id=project.id, is_active=True).order_by(Location.id).all()
            depot, points = validate_locations(loc)
            ids = [depot.id] + [p.id for p in points]
            matrix = build_distance_matrix(loc)
            save_distance_matrix(s, project.id, loc, matrix)
            route, algorithm = optimize(ids, matrix, "Nearest Neighbor + 2-opt")
            validate_route(route, depot.id, [p.id for p in points])
            baseline = ids + [ids[0]]
            metrics = route_metrics(route, matrix, average_speed=speed)
            comparison = compare(baseline, route, matrix)
            saved = save_route(s, project.id, route, algorithm, matrix, average_speed=speed)
            st.session_state.update({
                "scenario_id": project.id,
                "route": route,
                "baseline": baseline,
                "metrics": metrics,
                "comparison": comparison,
                "algorithm": algorithm,
                "locations": loc,
                "route_id": saved.id,
            })
            st.success("Demo loaded and optimized. Open Results to see the route animation.")
            st.rerun()
    with c2:
        if st.button("↺ Reset Demo", use_container_width=True):
            project = load_demo_scenario(s, reset=True)
            for key in ("route", "baseline", "metrics", "comparison", "algorithm", "locations", "route_id"):
                st.session_state.pop(key, None)
            st.session_state["scenario_id"] = project.id
            st.success("Demo data reset to the original offline dataset.")
            st.rerun()

    st.subheader("Settings")
    new_speed = st.number_input("Average vehicle speed (km/h)", min_value=0.1, value=float(speed), step=1.0)
    if st.button("Save settings"):
        set_average_speed(s, new_speed)
        st.success("Average vehicle speed saved.")
        st.rerun()

    project = s.query(Location).filter_by(is_active=True).first()
    if project:
        active = s.query(Location).filter_by(project_id=project.project_id, is_active=True).order_by(Location.id).all()
        st.metric("Active locations", len(active))
        st.caption(f"Scenario: {s.get(type(project.project_id), project.project_id) if False else project.project_id}")
        if st.session_state.get("route"):
            st.plotly_chart(
                route_figure(active, st.session_state["route"]),
                use_container_width=True,
            )
    else:
        st.info("Click Start Demo or create a scenario to begin.")
finally:
    s.close()
