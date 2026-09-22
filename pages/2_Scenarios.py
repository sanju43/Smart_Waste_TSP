import streamlit as st
from database.database import get_session
from database.models import Project
from services.scenario_service import get_projects

st.title("Scenarios")
s = get_session()
try:
    projects = get_projects(s)
    if not projects:
        st.info("No scenarios yet. Create one below.")
    labels = {f"{p.id}: {p.name}": p.id for p in projects}
    if labels:
        current = st.session_state.get("scenario_id", projects[0].id)
        selected = st.selectbox("Active scenario", list(labels), index=max(0, [p.id for p in projects].index(current) if current in [p.id for p in projects] else 0))
        st.session_state["scenario_id"] = labels[selected]
        st.success(f"Active scenario: {selected}")

    st.subheader("Create scenario")
    with st.form("new_scenario"):
        name = st.text_input("Scenario name")
        desc = st.text_area("Description")
        if st.form_submit_button("Create scenario") and name.strip():
            p = Project(name=name.strip(), description=desc.strip() or None)
            s.add(p)
            s.commit()
            st.session_state["scenario_id"] = p.id
            st.success("Scenario created and selected.")
            st.rerun()

    if projects:
        st.subheader("Manage scenarios")
        selected_id = st.session_state["scenario_id"]
        p = s.get(Project, selected_id)
        with st.form("edit_scenario"):
            name = st.text_input("Name", value=p.name)
            desc = st.text_area("Description", value=p.description or "")
            if st.form_submit_button("Save changes"):
                p.name = name.strip()
                p.description = desc.strip() or None
                s.commit()
                st.success("Scenario updated.")
        if len(projects) > 1 and st.button("Delete active scenario"):
            s.delete(p)
            s.commit()
            st.session_state.pop("scenario_id", None)
            st.rerun()
finally:
    s.close()
