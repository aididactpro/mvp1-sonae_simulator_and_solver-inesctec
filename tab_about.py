"""Tab 3 — About the project, credits and literature."""

import streamlit as st


def render():
    st.markdown("""
    <div class="hero">
      <h2>About this project</h2>
      <p>A multi-objective route-planning simulator for in-store picking, built around the
         mACO1 ant colony optimisation algorithm.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown("#### The problem & context")
        st.markdown("""
This simulator was built for the **MVP1 evaluation of the SONAE use case** within the
**PEER project**. It models a (Matosinhos) retail store as a graph in which every edge
carries both a **distance** and a **travel-time** cost, and a shopper must collect a
predefined shopping list and reach the checkout.

The original simulator optimised a **single** objective at a time (distance *or* time)
with a Nearest-Neighbour heuristic. This version adds an **mACO1 multi-objective**
solver that returns the **whole Pareto front** of picking routes — the set of routes
that cannot be improved on one objective without sacrificing the other (e.g. a *short
but slow* route through the congested core vs. a *longer but faster* route via the clear
perimeter lanes).
        """)

        st.markdown("#### What's inside")
        st.markdown("""
- **Planner 1** — the direct planner: pick a list, get the Pareto front, click a route.
- **Guided Planner** — a learning journey from *what is multi-objective picking?* through
  a beginner assignment to an advanced research playground.
- **mACO1 solver** — dual pheromone matrices, RANDOM aggregation, weighted-sum heuristic,
  MMAS trail limits and a mixed best-so-far schedule, adapted from a validated Python port
  of the reference C implementation.
        """)

        st.markdown("#### Credits")
        st.markdown("""
- **Research lead:** Mehrdad Asadi — *(further details TBC)*
- **Development:** Arno Vinkovic
- **VUB Artificial Intelligence Research Group**
- Original SONAE/PEER picking simulator: the upstream MVP1 project team *(TBC)*
        """)

    with c2:
        st.markdown("#### Key literature")
        st.markdown("""
- **López-Ibáñez, M. & Stützle, T. (2012).** *The Automatic Design of Multi-Objective
  Ant Colony Optimization Algorithms.* IEEE Transactions on Evolutionary Computation.
  — the **mACO** family this work implements.
- **moaco software** — reference C implementation & docs:
  [lopez-ibanez.eu/moaco](https://lopez-ibanez.eu/moaco)
- **Iredi, Merkle & Middendorf (2001).** *Bi-criterion optimization with multi-colony
  ant algorithms* (BicriterionAnt).
- **Dorigo & Stützle (2004).** *Ant Colony Optimization*, MIT Press — ACO & MAX–MIN Ant
  System (MMAS) foundations.
- **Pareto efficiency / multi-objective optimisation** — background for the dominance
  and Pareto-front concepts used throughout.
        """)

        st.markdown("#### Resources")
        st.markdown("""
- Upstream repository: `mvp1-sonae_simulator_and_solver-inesctec`
- Quality indicators (hypervolume, IGD): **moocore** (López-Ibáñez)
        """)

        st.info("PEER project • SONAE use case • INESC TEC • VUB AI Research Group", icon="🤝")

    st.divider()
    st.caption(
        "Disclaimer: products and store layout are fictitious and used only for the MVP1 "
        "demonstration. The travel-time/congestion model is an illustrative assumption for "
        "showcasing the multi-objective trade-off, not measured store data. "
        "Details marked *TBC* to be confirmed with the project team."
    )
