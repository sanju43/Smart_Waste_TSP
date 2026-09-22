import plotly.graph_objects as go

def comparison_chart(baseline, improved):
    fig = go.Figure(go.Bar(x=["Baseline", "Improved"], y=[baseline, improved], text=[f"{baseline:.2f}", f"{improved:.2f}"], textposition="auto"))
    fig.update_layout(yaxis_title="Distance")
    return fig
