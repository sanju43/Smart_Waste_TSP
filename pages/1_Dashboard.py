import streamlit as st
from database.database import get_session
from database.models import Project, Location
st.title("Dashboard")
s=get_session()
try:
    p=s.query(Project).first(); n=s.query(Location).filter_by(project_id=p.id,is_active=True).count() if p else 0
    a,b=st.columns(2); a.metric("Active locations", n); b.metric("Project", p.name if p else "Not seeded")
finally: s.close()
st.markdown("Add points → calculate distance → optimize route → compare results.")
