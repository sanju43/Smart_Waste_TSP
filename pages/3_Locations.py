import streamlit as st
from database.database import get_session
from database.models import Project, Location
st.title("Locations")
s=get_session()
try:
    p=s.query(Project).first()
    if not p: st.error("Run python database/seed.py first."); st.stop()
    with st.form("add"):
        name=st.text_input("Name"); typ=st.selectbox("Type",["Collection","Depot"]); x=st.number_input("X",0.0); y=st.number_input("Y",0.0); waste=st.number_input("Waste (kg)",0.0); priority=st.slider("Priority",1,5,1)
        if st.form_submit_button("Add location"):
            s.add(Location(project_id=p.id,name=name,type=typ,x=x,y=y,waste_kg=waste,priority=priority)); s.commit(); st.rerun()
    rows=s.query(Location).filter_by(project_id=p.id).all()
    st.dataframe([{"ID":r.id,"Name":r.name,"Type":r.type,"X":r.x,"Y":r.y,"Waste kg":r.waste_kg,"Priority":r.priority,"Active":r.is_active} for r in rows],use_container_width=True)
finally: s.close()
