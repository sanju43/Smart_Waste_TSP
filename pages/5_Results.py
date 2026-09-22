import streamlit as st

from components.route_chart import comparison_chart
from components.simulation import route_animation_figure

st.title("Results & Comparison")

c = st.session_state.get("comparison")
m = st.session_state.get("metrics")
route = st.session_state.get("route")
locations = st.session_state.get("locations")

if not c:
    st.info("Run the optimizer first.")
    st.stop()

a, b, d, e = st.columns(4)
a.metric("Baseline", f"{c['baseline']:.2f}")
b.metric("Improved", f"{c['improved']:.2f}")
d.metric("Saved", f"{c['saved']:.2f}")
e.metric("% saved", f"{c['percent_saved']:.1f}%")

st.plotly_chart(
    comparison_chart(c["baseline"], c["improved"]),
    use_container_width=True,
)
st.write("Estimated travel time:", f"{m['estimated_minutes']:.1f} minutes")

if route and locations:
    st.divider()
    st.subheader("🚛 Route Simulation")
    st.caption(
        "Press ▶ Play route to animate the collection vehicle. "
        "Use the slider to inspect each stop."
    )
    st.plotly_chart(
        route_animation_figure(locations, route),
        use_container_width=True,
    )
else:
    st.info("Optimize a route to enable the route simulation.")
