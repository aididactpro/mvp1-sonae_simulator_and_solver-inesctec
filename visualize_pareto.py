"""Visualisations for the multi-objective (mACO1) picking planner.

Two Plotly figures:

* ``store_map``     -- the store layout with the *actual walked route* of one
  Pareto solution drawn on top, plus a light shading of the congested core so
  it is visually obvious why a longer path can be faster.
* ``pareto_scatter`` -- the Pareto front (distance vs time); each marker is one
  non-dominated route, the selected one highlighted.
"""

from __future__ import annotations

import plotly.graph_objects as go

# Palette — VUB AI Research Group (see branding.py)
ROUTE = "#003399"         # VUB blue — the walked route
ACCENT = "#FF6600"        # VUB orange — selected Pareto point
ACCENT_SOFT = "rgba(255,102,0,0.15)"
INK = "#1f2937"
MUTED = "#9ca3af"
FAST = "#16a34a"
CONGEST = "rgba(239,68,68,0.10)"
GRID = "rgba(0,51,153,0.18)"


def _shelf_shapes(max_column, horizontal):
    """Reconstruct the shelf rectangles of the store layout."""
    shapes = []
    positions = [i for i, v in enumerate(horizontal) if v == 1]
    for i, position in enumerate(positions[:-1]):
        nxt = positions[i + 1]
        # left & right perimeter shelves
        for x0, x1 in [(0, 0.6), (max_column + 0.4, max_column + 1)]:
            shapes.append(dict(type="rect", x0=x0, y0=position + 1.4,
                               x1=x1, y1=nxt + 0.6, line=dict(color=MUTED, width=0.5),
                               fillcolor="rgba(203,213,225,0.55)", layer="below"))
        for j in range(max_column // 2):
            for off in (1.4, 2.0):
                shapes.append(dict(type="rect", x0=2 * j + off, y0=position + 1.4,
                                   x1=2 * j + off + 0.6, y1=nxt + 0.6,
                                   line=dict(color=MUTED, width=0.5),
                                   fillcolor="rgba(203,213,225,0.55)", layer="below"))
    return shapes


def store_map(G, nodes, products, route, v_0, v_end, max_column, horizontal,
              shopping_list, congestion_box=(4, 12, 2, 10)):
    """Render the store with ``route`` (a ParetoRoute) drawn on it."""
    pos = {i: data.coords for i, data in nodes.items()}
    fig = go.Figure()

    # --- congested core shading (explains the time/distance trade-off) ---
    xlo, xhi, ylo, yhi = congestion_box
    fig.add_shape(type="rect", x0=xlo - 0.5, y0=ylo - 0.5, x1=xhi + 0.5, y1=yhi + 0.5,
                  line=dict(width=0), fillcolor=CONGEST, layer="below")
    fig.add_annotation(x=(xlo + xhi) / 2, y=yhi + 0.1, text="🐢 congested core",
                       showarrow=False, font=dict(color="rgba(239,68,68,0.65)", size=11))

    # --- shelves ---
    for shp in _shelf_shapes(max_column, horizontal):
        fig.add_shape(shp)

    # --- faint walkable graph ---
    ex, ey = [], []
    for u, v in G.edges():
        ex += [pos[u][0], pos[v][0], None]
        ey += [pos[u][1], pos[v][1], None]
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines",
                             line=dict(width=0.6, color=GRID), hoverinfo="none"))

    # --- the actual walked route ---
    if route is not None and route.full_path:
        rx = [pos[n][0] for n in route.full_path]
        ry = [pos[n][1] for n in route.full_path]
        fig.add_trace(go.Scatter(
            x=rx, y=ry, mode="lines",
            line=dict(width=4, color=ROUTE),
            hoverinfo="none", name="route"))

    # --- product markers on the shopping list ---
    if route is not None:
        for k in shopping_list:
            node = products[k]['locations'][0]
            fig.add_annotation(x=pos[node][0], y=pos[node][1],
                               text=products[k]['icon'], showarrow=False,
                               font=dict(size=22))

    # --- start & checkout ---
    fig.add_annotation(x=pos[v_0][0], y=pos[v_0][1], text="🧍", showarrow=False,
                       font=dict(size=30))
    fig.add_annotation(x=pos[v_end][0], y=pos[v_end][1], text="💰", showarrow=False,
                       font=dict(size=28))

    fig.update_layout(
        showlegend=False, height=560,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-0.6, max_column + 1.6]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   scaleanchor="x", scaleratio=1),
    )
    return fig


def pareto_scatter(routes, selected_idx=None):
    """Scatter of the Pareto front; marker `i` is ``routes[i]``."""
    fig = go.Figure()
    if not routes:
        return fig

    import units
    xs = [units.meters(r.distance) for r in routes]
    ys = [units.minutes(r.time) for r in routes]

    # connecting step line (the front is sorted by distance)
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines", line=dict(color=MUTED, width=1, dash="dot"),
        hoverinfo="none"))

    text = [f"#{i+1}<br>{d:.0f} m<br>{t:.1f} min"
            for i, (d, t) in enumerate(zip(xs, ys))]
    colors = [ACCENT if i == selected_idx else ROUTE for i in range(len(routes))]
    sizes = [20 if i == selected_idx else 12 for i in range(len(routes))]

    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers+text",
        marker=dict(size=sizes, color=colors,
                    line=dict(width=2, color="white")),
        text=[f"{i+1}" for i in range(len(routes))],
        textposition="middle center",
        textfont=dict(color="white", size=10),
        customdata=list(range(len(routes))),
        hovertext=text, hoverinfo="text"))

    fig.update_layout(
        height=560, showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Distance walked (m)  ·  ← shorter is better",
                   gridcolor=GRID, zeroline=False),
        yaxis=dict(title="Time (min)  ·  ← faster is better",
                   gridcolor=GRID, zeroline=False),
    )
    return fig
