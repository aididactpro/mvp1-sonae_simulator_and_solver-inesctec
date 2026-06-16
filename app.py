"""Multi-objective picking planner (mACO1) — SONAE MVP1 simulator.

Given a start position, the fixed checkout and a shopping list, this app uses
the mACO1 multi-objective ant colony algorithm to compute the **Pareto front**
of picking routes: the set of routes that trade off total walked *distance*
against total *time* without dominating each other.  Pick any point on the
front to see that exact route drawn on the store map.

Run with:  ``streamlit run app.py``
(The original interactive navigation simulator is kept in ``app_navigation.py``.)
"""

import streamlit as st

from graph import create_graph
from product_catalogue import read_products_from_excel
from maco_solver import maco_pareto, MacoParams
from visualize_pareto import store_map, pareto_scatter

# --------------------------------------------------------------------------- #
# Page + theme
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="SONAE • Multi-objective Picking Planner",
                   page_icon="🛒", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 1rem; max-width: 1400px;}
.hero {
  background: linear-gradient(110deg, #E2231A 0%, #b3140d 55%, #7a0c08 100%);
  border-radius: 16px; padding: 22px 28px; color: #fff;
  box-shadow: 0 10px 30px rgba(226,35,26,0.25); margin-bottom: 18px;
}
.hero h1 {font-size: 1.55rem; margin: 0 0 4px 0; font-weight: 700;}
.hero p  {margin: 0; opacity: 0.92; font-size: 0.95rem;}
.cards {display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 8px;}
.card {
  background: #fff; border: 1px solid #eef0f3; border-radius: 14px;
  padding: 14px 16px; box-shadow: 0 2px 10px rgba(17,24,39,0.04);
}
.card .label {color:#6b7280; font-size:0.72rem; text-transform:uppercase; letter-spacing:.04em;}
.card .value {color:#111827; font-size:1.5rem; font-weight:700; line-height:1.1;}
.card .unit  {color:#9ca3af; font-size:0.8rem; font-weight:500;}
.panel-title {font-weight:700; color:#1f2937; margin: 6px 0 2px 2px;}
.badge {display:inline-block; background:#fef2f2; color:#E2231A; border-radius:999px;
        padding:2px 10px; font-size:0.75rem; font-weight:600; margin-left:6px;}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# Store (cached) — layout constants come from the original simulator
# --------------------------------------------------------------------------- #
V_PAY = [109]
MEAT_STATION, FISH_STATION = 98, 102
V_FROZEN = [63, 71, 79, 87]
V_FRESH = [68, 76, 84, 92, 79, 77, 85, 93]
HORIZONTAL = [1, 2, 2, 2, 2, 1, 2, 2, 2, 2, 1]
MAX_COLUMN = 15


@st.cache_resource(show_spinner=False)
def get_store():
    products = read_products_from_excel('products.xlsx')
    G, nodes = create_graph(HORIZONTAL, MAX_COLUMN, products, V_PAY,
                            V_FROZEN, V_FRESH, MEAT_STATION, FISH_STATION)
    return products, G, nodes


@st.cache_data(show_spinner=False)
def solve(list_key, v_0, num_ants, max_iter, seed):
    """Cached mACO1 run keyed on the hashable inputs."""
    products, G, _nodes = get_store()
    instance = {'graph': G, 'products': products, 'K': list(list_key),
                'V_pay': V_PAY, 'v_0': v_0, 'target': 'min_distance'}
    res = maco_pareto(instance, MacoParams(num_ants=num_ants, max_iter=max_iter, seed=seed))
    return res


products, G, nodes = get_store()
product_ids = list(products.keys())

# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
st.markdown("""
<div class="hero">
  <h1>🛒 Multi-objective Picking Planner</h1>
  <p>mACO1 ant colony optimisation — the full Pareto front of picking routes,
     trading off <b>walking distance</b> against <b>time</b> for your shopping list.</p>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# Sidebar controls
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.subheader("🧺 Shopping list")
    selected = st.multiselect(
        "Products to pick",
        options=product_ids,
        default=[1, 7, 20, 35, 50],
        format_func=lambda pid: f"{products[pid]['name']} {products[pid]['icon']}",
    )

    st.subheader("📍 Start & finish")
    start_options = [n for n in nodes.keys() if n not in V_PAY]
    v_0 = st.selectbox("Start position (node)", options=start_options, index=0)
    st.caption(f"Finish is fixed at the checkout 💰 (node {V_PAY[0]}).")

    with st.expander("⚙️ mACO1 settings"):
        num_ants = st.slider("Ants per iteration", 30, 120, 60, step=30)
        max_iter = st.slider("Iterations", 50, 400, 150, step=50)
        seed = st.number_input("Random seed", value=1, step=1)

    with st.expander("ℹ️ How to read this"):
        st.markdown(
            "- Each point on the **Pareto front** is a route that is *not beaten* "
            "on both objectives at once.\n"
            "- A **short** route may cut through the congested core (slow); a "
            "**fast** route detours via the clear perimeter lanes (longer).\n"
            "- Click a point to draw that exact route on the map."
        )

# --------------------------------------------------------------------------- #
# Empty state
# --------------------------------------------------------------------------- #
if not selected:
    st.info("👈 Add a few products to your shopping list to compute the Pareto front.")
    st.stop()

# --------------------------------------------------------------------------- #
# Solve
# --------------------------------------------------------------------------- #
with st.spinner("Running mACO1…"):
    res = solve(tuple(selected), int(v_0), int(num_ants), int(max_iter), int(seed))
routes = res["routes"]

# selection state
if "sel_idx" not in st.session_state:
    st.session_state.sel_idx = 0
st.session_state.sel_idx = min(st.session_state.sel_idx, len(routes) - 1)

# --------------------------------------------------------------------------- #
# Metric cards
# --------------------------------------------------------------------------- #
sel = routes[st.session_state.sel_idx]
d_min = min(r.distance for r in routes)
t_min = min(r.time for r in routes)
st.markdown(f"""
<div class="cards">
  <div class="card"><div class="label">Pareto routes</div>
       <div class="value">{len(routes)}</div></div>
  <div class="card"><div class="label">Selected distance</div>
       <div class="value">{sel.distance:.0f} <span class="unit">steps</span></div></div>
  <div class="card"><div class="label">Selected time</div>
       <div class="value">{sel.time:.0f} <span class="unit">min</span></div></div>
  <div class="card"><div class="label">Best possible</div>
       <div class="value">{d_min:.0f}<span class="unit">st</span> / {t_min:.0f}<span class="unit">min</span></div></div>
  <div class="card"><div class="label">Solver</div>
       <div class="value">{res['elapsed']:.2f}<span class="unit">s</span></div>
       <div class="unit">{res['n_iter']} iters · {res['n_stops']} stops</div></div>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# Map + Pareto front
# --------------------------------------------------------------------------- #
col_map, col_par = st.columns([1.25, 1])

with col_par:
    st.markdown('<div class="panel-title">Pareto front '
                '<span class="badge">click a point</span></div>', unsafe_allow_html=True)
    fig = pareto_scatter(routes, st.session_state.sel_idx)
    event = st.plotly_chart(fig, use_container_width=True, key="pareto",
                            on_select="rerun")
    # update selection from a click on the scatter
    try:
        pts = event["selection"]["points"]
        if pts:
            cd = pts[0].get("customdata")
            idx = (cd[0] if isinstance(cd, (list, tuple)) else cd)
            if idx is None:
                idx = pts[0].get("point_index", st.session_state.sel_idx)
            st.session_state.sel_idx = int(idx)
    except (KeyError, TypeError, IndexError):
        pass

with col_map:
    st.markdown('<div class="panel-title">Store map — selected route</div>',
                unsafe_allow_html=True)
    sel = routes[st.session_state.sel_idx]
    map_fig = store_map(G, nodes, products, sel, int(v_0), V_PAY[0],
                        MAX_COLUMN, HORIZONTAL, selected)
    st.plotly_chart(map_fig, use_container_width=True, key="map")

# --------------------------------------------------------------------------- #
# Route table
# --------------------------------------------------------------------------- #
st.markdown('<div class="panel-title">All Pareto-optimal routes</div>',
            unsafe_allow_html=True)
table = []
for i, r in enumerate(routes):
    tag = "⬅ selected" if i == st.session_state.sel_idx else ""
    profile = ("shortest" if r.distance == d_min else
               "fastest" if r.time == t_min else "balanced")
    table.append({"#": i + 1, "Distance (steps)": round(r.distance, 1),
                  "Time (min)": round(r.time, 1), "Profile": profile,
                  "Stops (order)": " → ".join(str(n) for n in r.stop_order),
                  "": tag})
st.dataframe(table, use_container_width=True, hide_index=True)
