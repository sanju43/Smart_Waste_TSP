PRESENTATION_STEPS = [
    {
        "title": "The problem",
        "body": "A waste vehicle starts at the depot, visits every collection point, and returns to the depot. The order of visits changes the total travel distance.",
    },
    {
        "title": "The input",
        "body": "The exhibition demo uses one depot and six collection points on a synthetic X/Y coordinate grid. The model is deterministic and works offline.",
    },
    {
        "title": "Measure distance",
        "body": "The system builds a distance matrix. For two points, the educational model uses Euclidean distance: d = sqrt((x2-x1)^2 + (y2-y1)^2).",
    },
    {
        "title": "Optimize the route",
        "body": "The default exhibition algorithm starts with Nearest Neighbor and improves the route with 2-opt. It is a heuristic, so it is not guaranteed to be globally optimal.",
    },
    {
        "title": "Compare the result",
        "body": "The application compares the input-order baseline with the optimized route using total distance, estimated travel time, and collection stops.",
    },
    {
        "title": "See the vehicle move",
        "body": "The final stage uses the existing offline Plotly route animation so visitors can see the vehicle progress through each stop and return to the depot.",
    },
]


def get_presentation_steps():
    """Return immutable exhibition step definitions for the Presentation page."""
    return [dict(step) for step in PRESENTATION_STEPS]
