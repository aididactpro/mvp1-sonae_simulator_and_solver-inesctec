"""Tab 2 — Guided Planner: learn multi-objective picking from scratch.

A scaffolded journey: what-it-is intro with pop-up hints -> a beginner
assignment -> an advanced research playground -> an honest UX/feature
assessment. Modelled on the lab's Job-Shop scheduling demo UX.
"""

import streamlit as st

from store import get_store, solve, true_front, V_PAY, MAX_COLUMN, HORIZONTAL, CONGESTION_BOX
from visualize_pareto import store_map, pareto_scatter

# A small, fixed list that yields a clear 3-point front for the lesson.
BEGINNER_LIST = [35, 36, 31, 26, 41]


def _hint(label, body):
    """Short pop-up hint (falls back to a tooltip on older Streamlit)."""
    try:
        with st.popover(f"💡 {label}"):
            st.markdown(body)
    except Exception:
        st.caption(f"💡 **{label}** — {body}")


def render():
    products, G, nodes = get_store()
    product_ids = list(products.keys())

    st.markdown("""
    <div class="hero">
      <h2>🎓 Guided Planner — from zero to multi-objective</h2>
      <p>New to this? Start at the top. We explain what the problem is, let you try a
         guided first task, then open a playground for deeper experiments.</p>
    </div>
    """, unsafe_allow_html=True)

    # =====================================================================
    # 1) WHAT IS IT
    # =====================================================================
    st.markdown('<div class="panel-title">1 · What is multi-objective picking?</div>',
                unsafe_allow_html=True)
    st.markdown("""
Imagine you walk into a supermarket with a **shopping list**. You want a *good* route to
collect everything and reach the checkout. But "good" can mean two different things:

- **Distance** — walk as few steps as possible.
- **Time** — finish as fast as possible.

These are **not the same**. A shortcut straight through a crowded aisle is *short* but
*slow*; going the long way around an empty aisle is *longer* but *faster*. When two goals
like this pull in different directions, we have a **multi-objective problem**.
    """)

    h1, h2, h3, h4 = st.columns(4)
    with h1:
        _hint("Objective", "A thing you want to make as good as possible — here, *distance* "
                           "and *time*. We **minimise** both.")
    with h2:
        _hint("Trade-off", "Improving one objective makes the other worse. You can't always "
                           "have the shortest **and** the fastest route at once.")
    with h3:
        _hint("Dominate", "Route A **dominates** route B if A is at least as good on *both* "
                          "objectives and strictly better on one. Dominated routes are never worth choosing.")
    with h4:
        _hint("Pareto front", "The set of routes that **nothing else dominates**. Each is a "
                             "legitimate 'best' depending on how much you value time vs distance.")

    st.markdown("""
    <div class="note">
    🧭 <b>The big idea:</b> instead of forcing you to choose distance <i>or</i> time up front,
    the planner returns <b>every</b> sensible compromise — the <b>Pareto front</b> — and lets
    <i>you</i> pick the balance you like.
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    # =====================================================================
    # 2) BEGINNER ASSIGNMENT
    # =====================================================================
    st.markdown('<div class="panel-title">2 · 🎒 Your first assignment '
                '<span class="badge">beginner</span></div>', unsafe_allow_html=True)
    st.markdown(
        "No prior knowledge needed. We use a fixed starter shopping list so everyone sees the "
        "same result. Follow the three steps."
    )

    names = ", ".join(f"{products[p]['name']} {products[p]['icon']}" for p in BEGINNER_LIST)
    st.markdown(f'<span class="step">1</span> Our list for this lesson: **{names}**, '
                'starting at the entrance and finishing at the checkout 💰.', unsafe_allow_html=True)

    res = solve(tuple(BEGINNER_LIST), 0, 60, 150, 1)
    routes = res["routes"]
    d_min = min(r.distance for r in routes)
    t_min = min(r.time for r in routes)
    shortest = min(routes, key=lambda r: r.distance)
    fastest = min(routes, key=lambda r: r.time)

    st.markdown('<span class="step">2</span> Here is the **Pareto front** the planner found, '
                'and the route on the map. Switch between the shortest and the fastest route 👇',
                unsafe_allow_html=True)

    pick = st.radio("Show route:", ["⬇️ Shortest (fewest steps)", "⚡ Fastest (least time)"],
                    horizontal=True, key="l2_pick")
    chosen = shortest if pick.startswith("⬇️") else fastest
    sel_idx = routes.index(chosen)

    ccol1, ccol2 = st.columns([1, 1.25])
    with ccol1:
        st.plotly_chart(pareto_scatter(routes, sel_idx), use_container_width=True, key="l2_b_scatter")
    with ccol2:
        st.plotly_chart(store_map(G, nodes, products, chosen, 0, V_PAY[0], MAX_COLUMN,
                                  HORIZONTAL, BEGINNER_LIST, CONGESTION_BOX),
                        use_container_width=True, key="l2_b_map")

    st.markdown('<span class="step">3</span> Now answer these — open each box to check.',
                unsafe_allow_html=True)
    extra_steps = fastest.distance - shortest.distance
    saved_min = shortest.time - fastest.time
    with st.expander("❓ How many routes are on the Pareto front?"):
        st.success(f"**{len(routes)}**. Each one is a different, sensible compromise between "
                   "distance and time — none is 'wrong'.")
    with st.expander("❓ Which route is shortest, and which is fastest?"):
        st.success(f"Shortest: **{shortest.distance:.0f} steps** (but **{shortest.time:.0f} min**).  \n"
                   f"Fastest: **{fastest.time:.0f} min** (but **{fastest.distance:.0f} steps**).")
    with st.expander("❓ What do you give up to go fast instead of short?"):
        st.success(f"Going fastest instead of shortest costs **{extra_steps:.0f} extra steps** "
                   f"but saves **{saved_min:.0f} minutes**. Whether that's worth it is *your* call — "
                   "that choice is exactly what the Pareto front hands back to you.")
    with st.expander("❓ Why is the shortest route slow? (look at the map)"):
        st.success("The shortest route cuts straight through the **congested core** (shaded). "
                   "The fastest route detours along the **clear perimeter lanes** — more steps, less time.")

    st.write("")

    # =====================================================================
    # 3) ADVANCED PLAYGROUND
    # =====================================================================
    st.markdown('<div class="panel-title">3 · 🔬 Research playground '
                '<span class="badge">advanced</span></div>', unsafe_allow_html=True)
    st.markdown(
        "Build any instance and probe the **mACO1** algorithm. Hover the 💡 hints for what each "
        "control does. When the instance is small enough we also compute the **exact** Pareto "
        "front by brute force, so you can judge how well mACO1 did."
    )

    pcol1, pcol2 = st.columns([1, 2])
    with pcol1:
        adv_list = st.multiselect(
            "Shopping list",
            options=product_ids,
            default=[1, 7, 20, 35, 50, 12],
            format_func=lambda pid: f"{products[pid]['name']} {products[pid]['icon']}",
            key="l2_adv_list",
        )
        start_opts = [n for n in nodes.keys() if n not in V_PAY]
        adv_start = st.selectbox("Start node", options=start_opts, index=0, key="l2_adv_start")

        a1, a2 = st.columns(2)
        with a1:
            _hint("Ants", "More ants build more candidate routes per iteration — broader search, "
                          "slower. mACO1 splits them across 3 weight groups (distance / balanced / time).")
        with a2:
            _hint("Iterations", "How many rounds of build → learn (deposit pheromone) → repeat. "
                                "More iterations = more refinement, up to a point.")
        num_ants = st.slider("Ants", 30, 120, 60, step=30, key="l2_adv_ants")
        max_iter = st.slider("Iterations", 50, 400, 150, step=50, key="l2_adv_iter")
        seed = st.number_input("Random seed", value=1, step=1, key="l2_adv_seed")
        _hint("MMAS & congestion", "mACO1 uses MAX–MIN Ant System pheromone limits and a mixed "
              "best-so-far schedule. The **time** objective is distance × *aisle congestion*: the "
              "central core is slow, the perimeter is fast — that's what creates the trade-off.")

    if not adv_list:
        with pcol2:
            st.info("👈 Pick at least one product to run the playground.")
        return

    res2 = solve(tuple(adv_list), int(adv_start), int(num_ants), int(max_iter), int(seed))
    routes2 = res2["routes"]
    tf = true_front(tuple(adv_list), int(adv_start))

    if "l2_adv_sel" not in st.session_state:
        st.session_state.l2_adv_sel = 0
    st.session_state.l2_adv_sel = min(st.session_state.l2_adv_sel, len(routes2) - 1)

    with pcol2:
        # quality vs exact front
        if tf is not None:
            found = {(round(r.distance, 1), round(r.time, 1)) for r in routes2}
            truth = {(round(d, 1), round(t, 1)) for d, t in tf}
            match = len(found & truth)
            quality = f"{match}/{len(truth)} exact Pareto points recovered"
            qicon = "✅" if match == len(truth) else "➖"
        else:
            quality = "instance too large for exact check"
            qicon = "🔢"

        st.markdown(f"""
        <div class="cards" style="grid-template-columns: repeat(4,1fr);">
          <div class="card"><div class="label">mACO1 front</div><div class="value">{len(routes2)}</div><div class="unit">routes</div></div>
          <div class="card"><div class="label">Solver time</div><div class="value">{res2['elapsed']:.2f}<span class="unit">s</span></div><div class="unit">{res2['n_iter']} iters</div></div>
          <div class="card"><div class="label">Stops</div><div class="value">{res2['n_stops']}</div></div>
          <div class="card"><div class="label">Quality {qicon}</div><div class="value" style="font-size:0.95rem;">{quality}</div></div>
        </div>
        """, unsafe_allow_html=True)

        mcol1, mcol2 = st.columns([1, 1.25])
        with mcol1:
            event = st.plotly_chart(pareto_scatter(routes2, st.session_state.l2_adv_sel),
                                    use_container_width=True, key="l2_adv_scatter", on_select="rerun")
            try:
                pts = event["selection"]["points"]
                if pts:
                    cd = pts[0].get("customdata")
                    idx = (cd[0] if isinstance(cd, (list, tuple)) else cd)
                    st.session_state.l2_adv_sel = int(idx if idx is not None else 0)
            except (KeyError, TypeError, IndexError):
                pass
        with mcol2:
            sel2 = routes2[st.session_state.l2_adv_sel]
            st.plotly_chart(store_map(G, nodes, products, sel2, int(adv_start), V_PAY[0],
                                      MAX_COLUMN, HORIZONTAL, adv_list, CONGESTION_BOX),
                            use_container_width=True, key="l2_adv_map")

        st.caption("Tip: lower the iterations or ants and watch the recovered-points quality drop — "
                   "a hands-on feel for the accuracy/effort trade-off of metaheuristics.")

    st.write("")

    # =====================================================================
    # 4) UX & FEATURE ASSESSMENT
    # =====================================================================
    st.markdown('<div class="panel-title">4 · 🧭 What\'s missing & how to improve it</div>',
                unsafe_allow_html=True)
    st.markdown("An honest assessment of this planner for **public** (learners) and **academic** "
                "(researchers) use — and a roadmap.")

    g1, g2 = st.columns(2)
    with g1:
        with st.expander("👥 For public / learners — UX gaps", expanded=False):
            st.markdown("""
- **Onboarding tour.** A one-time guided overlay (e.g. highlight the front, then the map) would
  beat a wall of text. *Missing.*
- **Plain-language toggle.** Hide jargon by default; reveal "researcher mode" terms on demand.
- **Live linked highlighting.** Hovering a Pareto point should pulse the matching route on the
  map (and vice-versa). Currently selection is click-only.
- **Narrated comparison.** "This route saves you 12 min for 8 extra steps" auto-generated for the
  selected point, not just in the assignment.
- **Accessibility.** Colour-blind-safe palette option, larger hit targets, keyboard navigation.
- **Mobile layout.** The two-column map+front does not reflow well on phones.
            """)
    with g2:
        with st.expander("🎓 For researchers / academic — feature gaps", expanded=False):
            st.markdown("""
- **Quality indicators.** Report **hypervolume** and **IGD+** (via `moocore`) and plot convergence
  over iterations, not just point counts.
- **Algorithm comparison.** Run BicriterionAnt / MACS / NSGA-II side by side on the same instance.
- **Constraints.** Honour precedence, first/last product, fresh/frozen-last and queue waits inside
  the multi-objective search (this version is source → checkout + list only).
- **Real path-level trade-offs.** Expose the per-leg bi-objective path options explicitly.
- **Batch experiments & export.** Multi-seed runs, CSV/JSON export of fronts, reproducible configs.
- **Bring-your-own instance.** Upload a store graph / product map (like the Job-Shop demo's file
  uploader).
            """)

    with st.expander("⚙️ Technical / modelling notes", expanded=False):
        st.markdown("""
- The **congestion time model** is an illustrative assumption, not measured data — it should be
  swappable for real walking-time / dwell-time observations.
- mACO1 parameters are exposed but **not auto-tuned**; an `irace`-style tuner would help.
- Brute-force exact-front check only runs for small instances (≤ 7 stops); larger ones rely on the
  metaheuristic alone.
- Caching keys on the shopping list + params; changing the congestion model needs a cache reset.
        """)
