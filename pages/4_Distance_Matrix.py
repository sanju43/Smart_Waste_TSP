import streamlit as st
import pandas as pd
from database.database import get_session
from database.models import Project, Location
from services.distance_service import build_distance_matrix
from services.route_service import save_distance_matrix

st.title("Distance Matrix")
s = get_session()
try:
    projects = s.query(Project).order_by(Project.id).all()
    if not projects:
        st.info("Create or seed a scenario first.")
        st.stop()
    ids = [p.id for p in projects]
    scenario_id = st.session_state.get("scenario_id", ids[0])
    if scenario_id not in ids:
        scenario_id = ids[0]
        st.session_state["scenario_id"] = scenario_id
    p = s.get(Project, scenario_id)
    loc = s.query(Location).filter_by(project_id=p.id, is_active=True).order_by(Location.id).all()
    if not loc:
        st.info("No active locations.")
        st.stop()

    matrix = build_distance_matrix(loc)
    save_distance_matrix(s, p.id, loc, matrix)
    labels = [f"{x.id} — {x.name}" for x in loc]
    frame = pd.DataFrame(
        [[matrix[a.id][b.id] for b in loc] for a in loc],
        index=labels,
        columns=labels,
    )
    st.caption("Offline Euclidean distance over the scenario X/Y coordinate grid.")
    st.dataframe(frame.style.format("{:.2f}"), use_container_width=True)
finally:
    s.close()
