# Picking Environment - General Overview

This simulator was built for the MVP1 evaluation of the SONAE use case in the PEER project. It uses a smaller store graph and a restricted list of fictitious products to collect early feedback on the picking route workflow and UI behavior.

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
