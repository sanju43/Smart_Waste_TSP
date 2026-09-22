import streamlit as st
from database.database import init_db

st.set_page_config(page_title="Smart Waste TSP", page_icon="♻️", layout="wide")
init_db()

st.title("♻️ Smart Waste Collection Route Optimizer")
st.subheader("Traveling Salesman Problem (TSP) — Coding-Only Science Exhibition")
st.info("Use the sidebar to open Dashboard, Scenarios, Locations, Optimizer, Results, Science Explanation, or Presentation Mode.")

c1, c2, c3 = st.columns(3)
c1.metric("Technology", "Python + Streamlit")
c2.metric("Optimization", "Nearest Neighbor + 2-opt")
c3.metric("Database", "SQLite")

st.markdown("### Exhibition Demo")
st.write("Create a depot and collection points, calculate distances, optimize the route, and compare the baseline with the improved route.")
