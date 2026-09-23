import streamlit as st
from database.database import get_session
from database.models import Project, Location
from algorithms.validators import find_duplicate_coordinates, validate_locations, validate_route
from services.distance_service import build_distance_matrix
from services.tsp_optimizer import optimize
from services.result_service import route_metrics, compare
from services.route_service import save_distance_matrix, save_route
from components.map_view import route_figure

st.title("Optimizer")
st.caption("Run a route only after the scenario passes validation.")
s = get_session()
try:
    projects = s.query(Project).order_by(Project.id).all()
    if not projects:
        st.info("Create or seed a scenario first.")
        st.stop()
    project_ids = [p.id for p in projects]
    scenario_id = st.session_state.get("scenario_id", project_ids[0])
    if scenario_id not in project_ids:
        scenario_id = project_ids[0]
        st.session_state["scenario_id"] = scenario_id
    p = s.get(Project, scenario_id)
    loc = s.query(Location).filter_by(project_id=p.id, is_active=True).order_by(Location.id).all()

    try:
        depot, points = validate_locations(loc)
    except ValueError as exc:
        st.error(f"Cannot optimize “{p.name}”: {exc}")
        st.info("Fix the scenario on the Locations page, then return here.")
        st.stop()

    duplicates = find_duplicate_coordinates(loc)
    if duplicates:
        names = "; ".join(", ".join(item.name for item in group) for group in duplicates)
        st.warning(
            "Duplicate coordinates detected. Zero-distance legs are allowed by the grid model, "
            f"but these locations share coordinates: {names}"
        )

    if len(points) == 1:
        st.info("Single collection point: the valid route is Depot → Point → Depot.")

    ids = [depot.id] + [x.id for x in points]
    matrix = build_distance_matrix(loc)

    try:
        save_distance_matrix(s, p.id, loc, matrix)
    except ValueError as exc:
        st.error(f"Distance matrix could not be saved: {exc}")
        st.stop()

    mode = st.selectbox(
        "Algorithm",
        ["Nearest Neighbor + 2-opt", "Exact (small N)"],
        help="Exact mode is intended only for small datasets; the heuristic is the default exhibition mode.",
    )
    if mode == "Exact (small N)" and len(ids) > 9:
        st.warning("Exact mode supports at most 9 nodes including the depot. Use Nearest Neighbor + 2-opt for larger scenarios.")
    if st.button("Optimize route", type="primary"):
        try:
            route, alg = optimize(ids, matrix, mode)
            validate_route(route, depot.id, [x.id for x in points])
            baseline = ids + [ids[0]]
            metrics = route_metrics(route, matrix)
            comparison = compare(baseline, route, matrix)
            saved = save_route(s, p.id, route, alg, matrix)
            st.session_state.update({
                "route": route, "baseline": baseline, "metrics": metrics,
                "comparison": comparison, "algorithm": alg,
                "route_id": saved.id, "scenario_id": p.id
            })
            st.success(f"Route saved to SQLite (Route #{saved.id}).")
        except (ValueError, KeyError) as exc:
            st.error(f"Optimization could not be completed: {exc}")
            st.info("No new route was saved. Correct the scenario or choose another algorithm.")

    if "route" in st.session_state and st.session_state.get("scenario_id") == p.id:
        st.success(f"Algorithm: {st.session_state['algorithm']}")
        # Re-query ORM objects in the current session instead of retaining detached
        # Location instances across Streamlit reruns.
        current_locations = (
            s.query(Location)
            .filter_by(project_id=p.id, is_active=True)
            .order_by(Location.id)
            .all()
        )
        st.plotly_chart(
            route_figure(current_locations, st.session_state["route"]),
            use_container_width=True,
        )
        st.write("Route:", " → ".join(str(i) for i in st.session_state["route"]))
finally:
    s.close()
