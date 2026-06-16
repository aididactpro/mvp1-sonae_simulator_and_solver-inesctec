"""Tab 1 — Planner 1: the direct multi-objective picking planner."""

import streamlit as st

from store import get_store, solve, V_PAY, MAX_COLUMN, HORIZONTAL, CONGESTION_BOX
from visualize_pareto import store_map, pareto_scatter
from units import meters, minutes


def render():
    products, G, nodes = get_store()
    product_ids = list(products.keys())

    st.markdown("""
    <div class="hero">
      <h2>Planner 1 — Multi-objective picking</h2>
      <p>mACO1 ant colony optimisation computes the full Pareto front of picking routes,
         trading <b>walking distance</b> against <b>time</b> for your shopping list.
         Click any point on the front to draw that route.</p>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1, 3])

    # ---- controls (compact, in-tab) ---------------------------------------
    with left:
        selected = st.multiselect(
            "🧺 Shopping list",
            options=product_ids,
            default=[1, 7, 20, 35, 50],
            format_func=lambda pid: f"{products[pid]['name']} {products[pid]['icon']}",
            key="p1_list",
        )
        start_options = [n for n in nodes.keys() if n not in V_PAY]
        v_0 = st.selectbox("📍 Start node", options=start_options, index=0, key="p1_start")
        with st.expander("⚙️ mACO1 settings"):
            num_ants = st.slider("Ants", 30, 120, 60, step=30, key="p1_ants")
            max_iter = st.slider("Iterations", 50, 400, 150, step=50, key="p1_iter")
            seed = st.number_input("Seed", value=1, step=1, key="p1_seed")

    if not selected:
        with right:
            st.info("👈 Add a few products to compute the Pareto front.")
        return

    with st.spinner("Running mACO1…"):
        res = solve(tuple(selected), int(v_0), int(num_ants), int(max_iter), int(seed))
    routes = res["routes"]

    if "p1_sel" not in st.session_state:
        st.session_state.p1_sel = 0
    st.session_state.p1_sel = min(st.session_state.p1_sel, len(routes) - 1)

    sel = routes[st.session_state.p1_sel]
    d_min = min(r.distance for r in routes)
    t_min = min(r.time for r in routes)

    with right:
        st.markdown(f"""
        <div class="cards">
          <div class="card"><div class="label">Pareto routes</div><div class="value">{len(routes)}</div></div>
          <div class="card"><div class="label">Selected distance</div><div class="value">{meters(sel.distance):.0f} <span class="unit">m</span></div></div>
          <div class="card"><div class="label">Selected time</div><div class="value">{minutes(sel.time):.1f} <span class="unit">min</span></div></div>
          <div class="card"><div class="label">Best possible</div><div class="value">{meters(d_min):.0f}<span class="unit">m</span> / {minutes(t_min):.1f}<span class="unit">min</span></div></div>
          <div class="card"><div class="label">Solver</div><div class="value">{res['elapsed']:.2f}<span class="unit">s</span></div><div class="unit">{res['n_iter']} iters · {res['n_stops']} stops</div></div>
        </div>
        """, unsafe_allow_html=True)

        col_map, col_par = st.columns([1.25, 1])
        with col_par:
            st.markdown('<div class="panel-title">Pareto front '
                        '<span class="badge">click a point</span></div>', unsafe_allow_html=True)
            event = st.plotly_chart(pareto_scatter(routes, st.session_state.p1_sel),
                                    use_container_width=True, key="p1_pareto", on_select="rerun")
            try:
                pts = event["selection"]["points"]
                if pts:
                    cd = pts[0].get("customdata")
                    idx = (cd[0] if isinstance(cd, (list, tuple)) else cd)
                    if idx is None:
                        idx = pts[0].get("point_index", st.session_state.p1_sel)
                    st.session_state.p1_sel = int(idx)
            except (KeyError, TypeError, IndexError):
                pass
        with col_map:
            st.markdown('<div class="panel-title">Store map — selected route</div>',
                        unsafe_allow_html=True)
            sel = routes[st.session_state.p1_sel]
            st.plotly_chart(store_map(G, nodes, products, sel, int(v_0), V_PAY[0],
                                      MAX_COLUMN, HORIZONTAL, selected, CONGESTION_BOX),
                            use_container_width=True, key="p1_map")

        st.markdown('<div class="panel-title">All Pareto-optimal routes</div>', unsafe_allow_html=True)
        table = []
        for i, r in enumerate(routes):
            profile = ("shortest" if r.distance == d_min else
                       "fastest" if r.time == t_min else "balanced")
            table.append({"#": i + 1, "Distance (m)": round(meters(r.distance)),
                          "Time (min)": round(minutes(r.time), 1), "Profile": profile,
                          "Stops (order)": " → ".join(str(n) for n in r.stop_order),
                          "": "⬅ selected" if i == st.session_state.p1_sel else ""})
        st.dataframe(table, use_container_width=True, hide_index=True)
