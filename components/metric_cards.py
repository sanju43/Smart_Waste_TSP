import streamlit as st

def show_metrics(metrics):
    a,b,c = st.columns(3)
    a.metric("Total distance", f"{metrics['total_distance']:.2f}")
    b.metric("Estimated time", f"{metrics['estimated_minutes']:.1f} min")
    c.metric("Stops", metrics['stops'])
