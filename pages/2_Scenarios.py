import streamlit as st
from database.database import get_session
from database.models import Project
st.title("Scenarios")
s=get_session()
try:
    for p in s.query(Project).all(): st.write(f"**{p.id}. {p.name}** — {p.description}")
    with st.form("new"):
        name=st.text_input("Scenario name")
        desc=st.text_area("Description")
        if st.form_submit_button("Create") and name:
            s.add(Project(name=name,description=desc)); s.commit(); st.success("Scenario created")
finally: s.close()
