import plotly.graph_objects as go

def route_figure(locations, route):
    by_id = {x.id: x for x in locations}
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[x.x for x in locations], y=[x.y for x in locations], mode="markers+text", text=[x.name for x in locations], textposition="top center", name="Locations"))
    pts = [by_id[i] for i in route]
    fig.add_trace(go.Scatter(x=[x.x for x in pts], y=[x.y for x in pts], mode="lines+markers", name="Route"))
    fig.update_layout(xaxis_title="X coordinate", yaxis_title="Y coordinate", height=520, legend=dict(orientation="h"))
    return fig
