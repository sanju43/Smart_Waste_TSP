import plotly.graph_objects as go

from services.route_simulation import animation_steps


def route_animation_figure(locations, route):
    """Build an offline Plotly route animation with play/pause controls."""
    steps = animation_steps(locations, route)
    if not steps:
        raise ValueError("A route is required for animation.")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[location.x for location in locations],
        y=[location.y for location in locations],
        mode="markers+text",
        text=[location.name for location in locations],
        textposition="top center",
        name="Locations",
    ))
    first = steps[0]
    fig.add_trace(go.Scatter(
        x=first["path_x"],
        y=first["path_y"],
        mode="lines+markers",
        name="Vehicle route",
    ))
    fig.add_trace(go.Scatter(
        x=[first["vehicle_x"]],
        y=[first["vehicle_y"]],
        mode="markers",
        marker={"size": 18, "symbol": "circle"},
        name="Vehicle",
    ))

    frames = []
    for step in steps:
        frames.append(go.Frame(
            name=str(step["sequence"]),
            data=[
                go.Scatter(x=step["path_x"], y=step["path_y"]),
                go.Scatter(
                    x=[step["vehicle_x"]],
                    y=[step["vehicle_y"]],
                    mode="markers",
                    marker={"size": 18, "symbol": "circle"},
                ),
            ],
            traces=[1, 2],
        ))

    fig.frames = frames
    fig.update_layout(
        title="Animated collection vehicle route",
        xaxis_title="X coordinate",
        yaxis_title="Y coordinate",
        height=560,
        legend={"orientation": "h"},
        updatemenus=[{
            "type": "buttons",
            "showactive": False,
            "x": 0.05,
            "y": 1.12,
            "buttons": [
                {
                    "label": "▶ Play route",
                    "method": "animate",
                    "args": [None, {
                        "frame": {"duration": 700, "redraw": True},
                        "transition": {"duration": 250},
                        "fromcurrent": True,
                        "mode": "immediate",
                    }],
                },
                {
                    "label": "⏸ Pause",
                    "method": "animate",
                    "args": [[None], {
                        "frame": {"duration": 0, "redraw": False},
                        "transition": {"duration": 0},
                        "mode": "immediate",
                    }],
                },
            ],
        }],
        sliders=[{
            "active": 0,
            "x": 0.1,
            "y": -0.08,
            "len": 0.85,
            "currentvalue": {"prefix": "Route step: "},
            "steps": [
                {
                    "label": str(step["sequence"]),
                    "method": "animate",
                    "args": [[str(step["sequence"])], {
                        "frame": {"duration": 0, "redraw": True},
                        "transition": {"duration": 0},
                        "mode": "immediate",
                    }],
                }
                for step in steps
            ],
        }],
    )
    return fig
