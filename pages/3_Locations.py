import math
import streamlit as st
from database.database import get_session
from database.models import Location, Project
from services.route_service import invalidate_routes


st.title("Locations")
st.caption("Add or edit synthetic X/Y points. Changes invalidate saved routes.")
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
    st.caption(f"Scenario: {p.name}")

    active_depots = s.query(Location).filter_by(project_id=p.id, type="Depot", is_active=True).count()
    with st.form("add_location"):
        name = st.text_input("Name")
        typ = st.selectbox("Type", ["Collection", "Depot"])
        x = st.number_input("X coordinate", value=0.0)
        y = st.number_input("Y coordinate", value=0.0)
        waste = st.number_input("Waste (kg)", min_value=0.0, value=0.0)
        priority = st.slider("Priority", 1, 5, 1)
        if st.form_submit_button("Add location"):
            name_clean = name.strip()
            if not name_clean:
                st.error("Name is required.")
            elif not math.isfinite(x) or not math.isfinite(y):
                st.error("X and Y coordinates must be finite numbers.")
            elif typ == "Depot" and active_depots:
                st.error("This scenario already has an active depot. Deactivate the current depot first.")
            else:
                s.add(Location(project_id=p.id, name=name_clean, type=typ, x=x, y=y, waste_kg=waste, priority=priority))
                s.commit()
                invalidate_routes(s, p.id)
                st.success("Location added. Rebuild/optimize the route to use the change.")
                st.rerun()

    rows = s.query(Location).filter_by(project_id=p.id).order_by(Location.id).all()
    st.subheader("Edit / deactivate locations")
    for row in rows:
        with st.expander(f"{row.id} — {row.name} ({row.type})"):
            with st.form(f"edit_{row.id}"):
                name = st.text_input("Name", value=row.name, key=f"name_{row.id}")
                typ = st.selectbox("Type", ["Collection", "Depot"], index=0 if row.type == "Collection" else 1, key=f"type_{row.id}")
                x = st.number_input("X", value=float(row.x), key=f"x_{row.id}")
                y = st.number_input("Y", value=float(row.y), key=f"y_{row.id}")
                waste = st.number_input("Waste kg", min_value=0.0, value=float(row.waste_kg), key=f"w_{row.id}")
                priority = st.slider("Priority", 1, 5, int(row.priority), key=f"p_{row.id}")
                active = st.checkbox("Active", value=row.is_active, key=f"a_{row.id}")
                if st.form_submit_button("Save"):
                    name_clean = name.strip()
                    other_depot = s.query(Location).filter(
                        Location.project_id == p.id,
                        Location.type == "Depot",
                        Location.is_active.is_(True),
                        Location.id != row.id,
                    ).count()
                    if not name_clean:
                        st.error("Name is required.")
                    elif not math.isfinite(x) or not math.isfinite(y):
                        st.error("X and Y coordinates must be finite numbers.")
                    elif typ == "Depot" and active and other_depot:
                        st.error("Only one active depot is allowed. Deactivate the existing depot first.")
                    elif row.type == "Depot" and row.is_active and (not active or typ != "Depot") and other_depot == 0:
                        st.error("Keep one active depot or add another depot before deactivating/changing this one.")
                    else:
                        row.name, row.type, row.x, row.y = name_clean, typ, x, y
                        row.waste_kg, row.priority, row.is_active = waste, priority, active
                        s.commit()
                        invalidate_routes(s, p.id)
                        st.success("Location updated; saved routes invalidated.")
                        st.rerun()

    st.dataframe([
        {"ID": r.id, "Name": r.name, "Type": r.type, "X": r.x, "Y": r.y,
         "Waste kg": r.waste_kg, "Priority": r.priority, "Active": r.is_active}
        for r in rows
    ], use_container_width=True)
finally:
    s.close()
