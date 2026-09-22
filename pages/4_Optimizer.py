import streamlit as st
from database.database import get_session
from database.models import Project, Location
from services.distance_service import build_distance_matrix
from services.tsp_optimizer import optimize
from services.result_service import route_metrics, compare
from components.map_view import route_figure
st.title("Optimizer")
s=get_session()
try:
    p=s.query(Project).first(); loc=s.query(Location).filter_by(project_id=p.id,is_active=True).all()
    if not loc: st.warning("No locations. Seed demo data first."); st.stop()
    depot=[x for x in loc if x.type=="Depot"]
    if len(depot)!=1: st.error("Exactly one active depot is required."); st.stop()
    ids=[depot[0].id]+[x.id for x in loc if x.type!="Depot"]
    matrix=build_distance_matrix(loc)
    mode=st.selectbox("Algorithm",["Nearest Neighbor + 2-opt","Exact (small N)"])
    if st.button("Optimize route",type="primary"):
        route, alg=optimize(ids,matrix,mode)
        baseline=ids+[ids[0]]
        m=route_metrics(route,matrix)
        cmp=compare(baseline,route,matrix)
        st.session_state["route"]=route; st.session_state["baseline"]=baseline; st.session_state["metrics"]=m; st.session_state["comparison"]=cmp; st.session_state["algorithm"]=alg; st.session_state["locations"]=loc
    if "route" in st.session_state:
        st.success(f"Algorithm: {st.session_state['algorithm']}")
        st.plotly_chart(route_figure(st.session_state["locations"],st.session_state["route"]),use_container_width=True)
        st.write("Route:", " → ".join(str(i) for i in st.session_state["route"]))
finally: s.close()
