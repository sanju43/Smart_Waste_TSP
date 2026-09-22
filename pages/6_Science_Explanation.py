import streamlit as st

st.title("Science Explanation")
st.caption("Traveling Salesman Problem (TSP) + Mathematical Modelling & Computational Thinking")

st.header("1. The problem")
st.write(
    "A waste vehicle starts from a depot and must visit multiple collection points. "
    "Different visit orders produce different total travel distances."
)

st.header("2. Scientific principle: Traveling Salesman Problem")
st.write(
    "TSP is a mathematical optimization problem in which locations are represented as nodes "
    "and the route visits each collection point once before returning to the starting depot."
)

with st.expander("Mathematical model", expanded=True):
    st.latex(r"d = \sqrt{(x_2-x_1)^2 + (y_2-y_1)^2}")
    st.write(
        "For this exhibition model, distance between two points is calculated using Euclidean "
        "distance on a synthetic X/Y coordinate grid."
    )

st.header("3. Our digital model")
st.write(
    "The project uses a synthetic coordinate grid instead of live city roads. "
    "This keeps the core demonstration deterministic, local, and fully offline."
)

st.header("4. How the optimizer works")
steps = [
    ("Step 1 — Input", "Set one depot and collection points with X/Y coordinates."),
    ("Step 2 — Distance matrix", "Build the distance matrix by calculating the pairwise distance between every location."),
    ("Step 3 — Baseline", "Use the input order as a reference route."),
    ("Step 4 — Nearest Neighbor", "From the current location, choose the nearest unvisited point."),
    ("Step 5 — 2-opt", "Try reversing route segments and keep changes that reduce total distance."),
    ("Step 6 — Return to depot", "Complete the route by returning to the starting depot."),
    ("Step 7 — Compare", "Show distance, estimated time, stop count, and route sequence."),
]
for title, description in steps:
    st.markdown(f"**{title}** — {description}")

st.header("5. Why route order matters")
st.write(
    "The same collection points can have different total route distances depending on visit order. "
    "The optimizer searches for an improved route using explainable heuristics."
)

st.warning(
    "Nearest Neighbor + 2-opt is a heuristic. It is not guaranteed to produce the globally shortest "
    "route. Exact mode is intended only for small datasets."
)

st.header("6. What this project does not model")
st.write(
    "This educational simulation does not represent real road networks, traffic, one-way streets, "
    "or live municipal routing. Its purpose is to demonstrate the TSP concept and computational thinking."
)

st.header("7. Exhibition takeaway")
st.success(
    "Input → Distance calculation → TSP-based route improvement → Visual comparison → "
    "Distance/time explanation"
)
