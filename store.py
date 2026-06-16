"""Shared store model + cached mACO1 runner used by all tabs."""

import streamlit as st

from graph import create_graph
from product_catalogue import read_products_from_excel
from maco_solver import maco_pareto, MacoParams

# Store layout constants (from the original simulator).
V_PAY = [109]
MEAT_STATION, FISH_STATION = 98, 102
V_FROZEN = [63, 71, 79, 87]
V_FRESH = [68, 76, 84, 92, 79, 77, 85, 93]
HORIZONTAL = [1, 2, 2, 2, 2, 1, 2, 2, 2, 2, 1]
MAX_COLUMN = 15
CONGESTION_BOX = (4, 12, 2, 10)   # xlo, xhi, ylo, yhi of the slow core


@st.cache_resource(show_spinner=False)
def get_store():
    products = read_products_from_excel('products.xlsx')
    G, nodes = create_graph(HORIZONTAL, MAX_COLUMN, products, V_PAY,
                            V_FROZEN, V_FRESH, MEAT_STATION, FISH_STATION)
    return products, G, nodes


@st.cache_data(show_spinner=False)
def solve(list_key, v_0, num_ants, max_iter, seed):
    """Cached mACO1 run keyed on hashable inputs."""
    products, G, _nodes = get_store()
    instance = {'graph': G, 'products': products, 'K': list(list_key),
                'V_pay': V_PAY, 'v_0': v_0, 'target': 'min_distance'}
    return maco_pareto(instance, MacoParams(num_ants=num_ants, max_iter=max_iter, seed=seed))


@st.cache_data(show_spinner=False)
def true_front(list_key, v_0, max_stops=7):
    """Exact Pareto front by brute force (order + per-leg path choice).

    Returns a sorted list of (distance, time) tuples, or None when the
    instance is too large to enumerate. Used to gauge mACO1 solution quality.
    """
    import itertools
    from maco_solver import _biobj_paths, _required_nodes, _dominates
    products, G, _nodes = get_store()
    instance = {'graph': G, 'products': products, 'K': list(list_key),
                'V_pay': V_PAY, 'v_0': v_0, 'target': 'min_distance'}
    s, stops, e, idx, _pn = _required_nodes(instance)
    if len(stops) > max_stops:
        return None

    legs = {(a, b): ([(0., 0., [idx[a]])] if a == b else _biobj_paths(G, idx[a], idx[b]))
            for a in range(len(idx)) for b in range(len(idx))}

    def prune(points):
        f = []
        for p in sorted(set((round(x[0], 3), round(x[1], 3)) for x in points)):
            if any(_dominates(c, p) for c in f):
                continue
            f = [c for c in f if not _dominates(p, c)]
            f.append(p)
        return sorted(f)

    glob = []
    for perm in itertools.permutations(stops):
        seq = [s] + list(perm) + [e]
        cur = [(0., 0.)]
        for k in range(len(seq) - 1):
            opts = [(d, t) for d, t, _ in legs[(seq[k], seq[k + 1])]]
            cur = prune([(a[0] + b[0], a[1] + b[1]) for a in cur for b in opts])
        glob.extend(cur)
    return prune(glob)
