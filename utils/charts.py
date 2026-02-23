# utils/charts.py — Plotly visualization helpers (dark theme)
import plotly.graph_objects as go
import plotly.express as px
import json

# ─── Dark theme layout defaults ──────────────────────────────────────
DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#E8EAED", size=12),
    margin=dict(l=20, r=20, t=40, b=20),
)

ACCENT_COLORS = ["#6C63FF", "#00D9FF", "#00E676", "#FFB740", "#FF5252", "#A78BFA"]


def render_gauge(value: float, title: str = "Score", max_val: int = 100) -> go.Figure:
    """Render an animated gauge chart for scores (DLS, confidence, etc.)."""
    if value <= 30:
        bar_color = "#00E676"
    elif value <= 60:
        bar_color = "#FFB740"
    else:
        bar_color = "#FF5252"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        number=dict(font=dict(size=48, color="#E8EAED")),
        title=dict(text=title, font=dict(size=16, color="#9AA0A6")),
        gauge=dict(
            axis=dict(range=[0, max_val], tickcolor="#9AA0A6", dtick=20,
                      tickfont=dict(color="#9AA0A6")),
            bar=dict(color=bar_color, thickness=0.7),
            bgcolor="rgba(45,49,67,0.5)",
            borderwidth=0,
            steps=[
                dict(range=[0, 30], color="rgba(0,230,118,0.08)"),
                dict(range=[30, 60], color="rgba(255,183,64,0.08)"),
                dict(range=[60, 100], color="rgba(255,82,82,0.08)"),
            ],
            threshold=dict(line=dict(color="#FF5252", width=3), thickness=0.8, value=75),
        ),
    ))
    fig.update_layout(**DARK_LAYOUT, height=280)
    return fig


def render_dna_radar(vector: list[float], twin_vector: list[float] = None,
                     labels: list[str] = None) -> go.Figure:
    """Render a radar chart for Case DNA vectors with optional twin overlay."""
    if labels is None:
        labels = ["Category", "Jurisdiction", "Claim Size", "Evidence", "Emotional", "Novelty"]

    fig = go.Figure()

    # Current case
    fig.add_trace(go.Scatterpolar(
        r=vector + [vector[0]],
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor="rgba(108,99,255,0.15)",
        line=dict(color="#6C63FF", width=2),
        name="Current Case",
    ))

    # Twin overlay
    if twin_vector:
        fig.add_trace(go.Scatterpolar(
            r=twin_vector + [twin_vector[0]],
            theta=labels + [labels[0]],
            fill="toself",
            fillcolor="rgba(0,217,255,0.1)",
            line=dict(color="#00D9FF", width=2, dash="dot"),
            name="Case Twin",
        ))

    fig.update_layout(
        **DARK_LAYOUT,
        height=350,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 1], gridcolor="#2D3143",
                            tickfont=dict(size=10, color="#9AA0A6")),
            angularaxis=dict(gridcolor="#2D3143",
                             tickfont=dict(size=11, color="#9AA0A6")),
        ),
        legend=dict(font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        showlegend=twin_vector is not None,
    )
    return fig


def render_dls_breakdown(reasons: dict) -> go.Figure:
    """Horizontal bar chart for DLS reason breakdown."""
    labels_map = {
        "lack_of_jurisdiction": "Jurisdiction Issues",
        "statute_of_limitations": "Statute of Limitations",
        "insufficient_evidence": "Insufficient Evidence",
        "frivolous_claim": "Frivolous Claim",
        "procedural_defect": "Procedural Defect",
    }
    names = [labels_map.get(k, k) for k in reasons.keys()]
    values = list(reasons.values())
    colors = ["#FF5252" if v > 60 else "#FFB740" if v > 30 else "#00E676" for v in values]

    fig = go.Figure(go.Bar(
        x=values,
        y=names,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v}%" for v in values],
        textposition="outside",
        textfont=dict(color="#E8EAED", size=12),
    ))
    fig.update_layout(
        **DARK_LAYOUT,
        height=280,
        xaxis=dict(range=[0, 105], gridcolor="#2D3143", zeroline=False),
        yaxis=dict(autorange="reversed"),
    )
    return fig


def render_emotion_timeline(turns: list[dict]) -> go.Figure:
    """Line chart showing emotional temperature over negotiation turns."""
    turn_nums = [t.get("turn", i + 1) for i, t in enumerate(turns)]
    temps = [t.get("emotion_score", 50) or 50 for t in turns]
    speakers = [t.get("speaker", "") for t in turns]

    color_map = {
        "Plaintiff Agent": "#6C63FF",
        "Defendant Agent": "#FFB740",
        "Mediator": "#00D9FF",
        "Judge": "#00E676",
    }

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=turn_nums, y=temps,
        mode="lines+markers",
        line=dict(color="#6C63FF", width=2),
        marker=dict(
            size=8,
            color=[color_map.get(s, "#9AA0A6") for s in speakers],
            line=dict(width=1, color="#0F1117"),
        ),
        text=speakers,
        hovertemplate="Turn %{x}<br>Temp: %{y}<br>Speaker: %{text}<extra></extra>",
    ))

    # Danger zone
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(255,82,82,0.08)",
                  line=dict(width=0), annotation_text="⚠️ Cooling-off Zone",
                  annotation_position="top right",
                  annotation_font=dict(color="#FF5252", size=10))

    fig.update_layout(
        **DARK_LAYOUT,
        height=300,
        xaxis=dict(title="Turn", gridcolor="#2D3143", dtick=1),
        yaxis=dict(title="Emotional Temperature", range=[0, 105], gridcolor="#2D3143"),
    )
    return fig


def render_conflict_graph(nodes: list[dict], edges: list[dict],
                          communities: dict = None) -> go.Figure:
    """Render a network graph visualization using Plotly."""
    import networkx as nx

    G = nx.MultiDiGraph()
    for n in nodes:
        G.add_node(n["id"], **n)
    for e in edges:
        G.add_edge(e["from_id"], e["to_id"], **e)

    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

    # Edge traces
    edge_x, edge_y = [], []
    for u, v, _ in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=1, color="rgba(108,99,255,0.3)"),
        hoverinfo="none",
    )

    # Node traces
    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    node_labels = [G.nodes[n].get("label", n) for n in G.nodes()]
    node_sizes = [max(15, min(40, G.nodes[n].get("case_count", 1) * 8)) for n in G.nodes()]

    if communities:
        node_colors = [communities.get(n, 0) for n in G.nodes()]
        colorscale = "Viridis"
    else:
        node_colors = [G.nodes[n].get("case_count", 1) for n in G.nodes()]
        colorscale = [[0, "#6C63FF"], [0.5, "#00D9FF"], [1, "#FF5252"]]

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        marker=dict(size=node_sizes, color=node_colors, colorscale=colorscale,
                    line=dict(width=1, color="#0F1117"),
                    colorbar=dict(title="Cases", tickfont=dict(color="#9AA0A6"))),
        text=node_labels,
        textposition="top center",
        textfont=dict(size=10, color="#E8EAED"),
        hovertemplate="%{text}<br>Cases: %{marker.color}<extra></extra>",
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        **DARK_LAYOUT,
        height=500,
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )
    return fig


def render_negotiation_offers(turns: list[dict]) -> go.Figure:
    """Area chart showing offer convergence over negotiation turns."""
    plaintiff_offers, defendant_offers, turn_nums = [], [], []

    for t in turns:
        if t.get("offer_amount") is not None:
            speaker = t.get("speaker", "")
            turn_num = t.get("turn", 0)
            if "Plaintiff" in speaker:
                plaintiff_offers.append({"turn": turn_num, "offer": t["offer_amount"]})
            elif "Defendant" in speaker:
                defendant_offers.append({"turn": turn_num, "offer": t["offer_amount"]})

    fig = go.Figure()
    if plaintiff_offers:
        fig.add_trace(go.Scatter(
            x=[p["turn"] for p in plaintiff_offers],
            y=[p["offer"] for p in plaintiff_offers],
            mode="lines+markers",
            name="Plaintiff",
            line=dict(color="#6C63FF", width=2),
            fill="tonexty" if defendant_offers else None,
            fillcolor="rgba(108,99,255,0.1)",
        ))
    if defendant_offers:
        fig.add_trace(go.Scatter(
            x=[d["turn"] for d in defendant_offers],
            y=[d["offer"] for d in defendant_offers],
            mode="lines+markers",
            name="Defendant",
            line=dict(color="#FFB740", width=2),
        ))

    fig.update_layout(
        **DARK_LAYOUT,
        height=300,
        xaxis=dict(title="Round", gridcolor="#2D3143", dtick=1),
        yaxis=dict(title="Offer Amount ($)", gridcolor="#2D3143"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def render_category_distribution(cases: list[dict]) -> go.Figure:
    """Donut chart for case category distribution."""
    from collections import Counter
    cats = Counter(c.get("category", "other") for c in cases)

    fig = go.Figure(go.Pie(
        labels=list(cats.keys()),
        values=list(cats.values()),
        hole=0.6,
        marker=dict(colors=ACCENT_COLORS[:len(cats)],
                    line=dict(color="#0F1117", width=2)),
        textfont=dict(color="#E8EAED"),
    ))
    fig.update_layout(**DARK_LAYOUT, height=300, showlegend=True,
                      legend=dict(bgcolor="rgba(0,0,0,0)"))
    return fig
