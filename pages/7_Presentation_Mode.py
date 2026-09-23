import time

import streamlit as st

from algorithms.validators import validate_locations, validate_route
from components.route_chart import comparison_chart
from components.simulation import route_animation_figure
from database.database import get_session
from database.models import Location
from services.demo_service import get_average_speed, load_demo_scenario
from services.distance_service import build_distance_matrix
from services.presentation_service import get_presentation_steps
from services.result_service import compare, route_metrics
from services.route_service import save_distance_matrix, save_route
from services.tsp_optimizer import optimize


st.set_page_config(page_title="Presentation Mode", page_icon="🎓", layout="wide")

st.markdown(
    """
    <style>
    .presentation-title {font-size: 3.2rem; font-weight: 800; line-height: 1.05; margin-bottom: .4rem;}
    .presentation-subtitle {font-size: 1.35rem; opacity: .82; margin-bottom: 1.2rem;}
    .presentation-step {font-size: 2.0rem; font-weight: 750; margin: .2rem 0 .7rem;}
    .presentation-body {font-size: 1.25rem; line-height: 1.55;}
    .presentation-label {font-size: 1rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="presentation-title">♻️ Smart Waste Collection Route Optimizer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="presentation-subtitle">Traveling Salesman Problem • Mathematical Modelling • Computational Thinking</div>',
    unsafe_allow_html=True,
)

session = get_session()
try:
    speed = get_average_speed(session)

    def prepare_demo():
        project = load_demo_scenario(session, reset=True)
        locations = (
            session.query(Location)
            .filter_by(project_id=project.id, is_active=True)
            .order_by(Location.id)
            .all()
        )
        depot, points = validate_locations(locations)
        ids = [depot.id] + [point.id for point in points]
        matrix = build_distance_matrix(locations)
        save_distance_matrix(session, project.id, locations, matrix)
        route, algorithm = optimize(ids, matrix, "Nearest Neighbor + 2-opt")
        validate_route(route, depot.id, [point.id for point in points])
        baseline = ids + [ids[0]]
        metrics = route_metrics(route, matrix, average_speed=speed)
        comparison = compare(baseline, route, matrix, average_speed=speed)
        saved = save_route(
            session,
            project.id,
            route,
            algorithm,
            matrix,
            average_speed=speed,
        )
        st.session_state.update(
            {
                "scenario_id": project.id,
                "route": route,
                "baseline": baseline,
                "metrics": metrics,
                "comparison": comparison,
                "algorithm": algorithm,
                "route_id": saved.id,
            }
        )

    controls = st.columns([1, 1, 4])
    with controls[0]:
        if st.button("▶ Start Presentation", type="primary", use_container_width=True):
            prepare_demo()
            st.session_state["presentation_running"] = True
            st.rerun()
    with controls[1]:
        if st.button("↺ Reset", use_container_width=True):
            for key in (
                "presentation_running",
                "presentation_complete",
                "route",
                "baseline",
                "metrics",
                "comparison",
                "algorithm",
                "locations",
                "route_id",
            ):
                st.session_state.pop(key, None)
            st.rerun()

    if not st.session_state.get("presentation_running"):
        st.info(
            "Press Start Presentation. The demo will automatically walk through the problem, "
            "input, distance model, optimization, comparison, and route simulation."
        )
        st.stop()

    steps = get_presentation_steps()
    stage = st.empty()
    detail = st.empty()
    progress = st.progress(0)

    for index, step in enumerate(steps, start=1):
        stage.markdown(
            f'<div class="presentation-label">Step {index} of {len(steps)}</div>'
            f'<div class="presentation-step">{step["title"]}</div>',
            unsafe_allow_html=True,
        )
        detail.markdown(
            f'<div class="presentation-body">{step["body"]}</div>',
            unsafe_allow_html=True,
        )
        progress.progress(index / len(steps))
        time.sleep(1.6)

    st.session_state["presentation_complete"] = True
    stage.markdown(
        '<div class="presentation-label">Complete</div>'
        '<div class="presentation-step">Optimized route ready for questions</div>',
        unsafe_allow_html=True,
    )
    detail.markdown(
        '<div class="presentation-body">Now explain the distance saved, estimated time, '
        'route order, and why Nearest Neighbor + 2-opt is a heuristic.</div>',
        unsafe_allow_html=True,
    )

    comparison = st.session_state["comparison"]
    metrics = st.session_state["metrics"]
    scenario_id = st.session_state.get("scenario_id")
    route = st.session_state["route"]
    locations = (
        session.query(Location)
        .filter_by(project_id=scenario_id, is_active=True)
        .order_by(Location.id)
        .all()
    ) if scenario_id else []

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Baseline distance", f'{comparison["baseline"]:.2f}')
    m2.metric("Improved distance", f'{comparison["improved"]:.2f}')
    m3.metric("Distance saved", f'{comparison["saved"]:.2f}')
    m4.metric("Estimated time", f'{metrics["estimated_minutes"]:.1f} min')

    st.plotly_chart(
        comparison_chart(comparison["baseline"], comparison["improved"]),
        use_container_width=True,
    )

    st.subheader("🚛 Route simulation")
    st.caption(
        f'Algorithm: {st.session_state["algorithm"]} · '
        f'Average speed: {speed:g} km/h · Stops: {metrics["stops"]}'
    )
    st.plotly_chart(
        route_animation_figure(locations, route),
        use_container_width=True,
    )
finally:
    session.close()
