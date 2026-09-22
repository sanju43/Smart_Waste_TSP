import streamlit as st


def show_metrics(metrics, comparison=None):
    if comparison:
        columns = st.columns(4)
        columns[0].metric("Improved distance", f"{comparison['improved']:.2f}")
        columns[1].metric("Estimated time", f"{metrics['estimated_minutes']:.1f} min")
        columns[2].metric("Stops", metrics["stops"])
        columns[3].metric("Distance saved", f"{comparison['saved']:.2f}")
        return

    columns = st.columns(3)
    columns[0].metric("Total distance", f"{metrics['total_distance']:.2f}")
    columns[1].metric("Estimated time", f"{metrics['estimated_minutes']:.1f} min")
    columns[2].metric("Stops", metrics["stops"])
