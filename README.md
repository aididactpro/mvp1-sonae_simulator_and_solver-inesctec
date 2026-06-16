# Picking Environment - General Overview

This simulator was built for the MVP1 evaluation of the SONAE use case in the PEER project. It uses a smaller store graph and a restricted list of fictitious products to collect early feedback on the picking route workflow and UI behavior.

---

## ✨ New: multi-objective picking planner (mACO1)

The simulator now ships with a **multi-objective route planner** that returns the
whole **Pareto front** of picking routes for a queried *source → checkout* and a
shopping list, instead of optimising a single objective. It uses an **mACO1**
multi-objective ant colony algorithm (adaptation of the validated Python port of
López-Ibáñez & Stützle, 2012) to trade off:

- **distance** — total walked length, and
- **time** — distance scaled by *aisle congestion*.

Each point on the front is a route that is not dominated on both objectives at
once — e.g. a *short but slow* route cutting through the congested core vs. a
*longer but faster* route detouring via the clear perimeter lanes. Click a point
on the Pareto chart to draw that exact route on the store map.

```bash
streamlit run app.py            # the new multi-objective planner (default)
streamlit run app_navigation.py # the original interactive navigation simulator
pytest test_maco_solver.py      # solver test suite
```

### What changed

| File | Change |
|------|--------|
| `graph.py` | Travel **time** is now `distance × aisle_congestion(...)` instead of `time == distance`, so the two objectives genuinely diverge and a Pareto front exists. Toggle with `create_graph(..., congestion=False)` for the legacy behaviour. |
| `maco_solver.py` | **New.** mACO1 multi-objective solver: dual pheromone matrices, RANDOM per-row aggregation, weighted-sum heuristic, MMAS trail limits and the mixed best-so-far schedule. Returns the Pareto front of concrete walks via `maco_pareto(instance)`; `maco_solver(instance)` is a drop-in single-route replacement for `heuristic_solver`. |
| `visualize_pareto.py` | **New.** Interactive Pareto scatter + a clean store map that draws the actual walked route and shades the congested core. |
| `app.py` | **Redesigned** UI focused on the Pareto planner (themed header, metric cards, clickable front, route table). The previous app is preserved as `app_navigation.py`. |
| `test_maco_solver.py` | **New.** Tests for front non-domination, path/cost consistency, determinism and a brute-force front match. |

### How the trade-off is modelled

Between two stops the shopper walks one physical path; a leg can have several
non-dominated (distance, time) paths (a short congested one, a longer clear one).
The solver searches visiting *orders* with mACO1 and, for each order, extracts the
exact non-dominated set of concrete walks, merging them into a global Pareto
archive. Every returned route therefore corresponds to one real, drawable walk
whose stored distance and time match the path actually taken (verified by tests).

---

## Getting Started

1. Create a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the Streamlit app:

```bash
streamlit run app.py
```

4. Open the URL shown by Streamlit in your browser.

---

## What this repository does

This repository implements a store picking simulation and route optimization prototype for a Matosinhos SONAE store layout. It includes: a Streamlit UI, a product catalogue reader, a store graph builder, route solvers, visualizations, and verification utilities.

---

## Main files and purpose

- `app.py`
  - Main Streamlit application.
  - Loads product data, creates the store graph, manages session state, and runs the solver.
  - Uses the heuristic solver by default.

- `exact_solver.py`
  - Exact mathematical programming solver using Gurobi.
  - Defines `mip_solver(instance)` for minimizing time or distance under constraints.
  - Not currently active in `app.py` by default.

- `heuristic_solver.py`
  - Heuristic route planner used by the Streamlit app.
  - Selects product locations and orders nodes using a nearest-neighbor-like approach.

- `graph.py`
  - Builds the store graph and node objects.
  - Defines `create_graph`, `get_movement_bools`, and JSON save/load utilities.

- `product_catalogue.py`
  - Reads product data from `products.xlsx` or JSON feed files.
  - Returns product metadata, category flags, and location lists.

- `verification.py`
  - Checks solver outputs and route feasibility.
  - Validates first/last nodes, precedence constraints, and time/distance metrics.

- `visualize_store_dynamic.py`
  - Plotly visualization helper for dynamic store layout and route display.

- `map.py`
  - Matplotlib-based store and route visualization helper.

- `products.xlsx`
  - Main product catalogue used by `app.py`.

---

## Notes

- If you want to use the exact solver, you need Gurobi installed and licensed.
- The app currently imports `heuristic_solver` by default; the exact solver call is commented out in `app.py`.
