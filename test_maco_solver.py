"""Tests for the mACO1 multi-objective picking solver.

Run with:  ``pytest test_maco_solver.py``  (or ``python test_maco_solver.py``)
"""

import itertools

import pytest

from graph import create_graph, aisle_congestion
from product_catalogue import read_products_from_excel
from maco_solver import (maco_pareto, maco_solver, MacoParams,
                         _biobj_paths, _dominates, _required_nodes)

V_PAY = [109]
HORIZONTAL = [1, 2, 2, 2, 2, 1, 2, 2, 2, 2, 1]
MAX_COLUMN = 15


@pytest.fixture(scope="module")
def store():
    products = read_products_from_excel('products.xlsx')
    G, nodes = create_graph(HORIZONTAL, MAX_COLUMN, products, V_PAY,
                            [63, 71, 79, 87], [68, 76, 84, 92, 79, 77, 85, 93],
                            98, 102)
    return products, G, nodes


def _instance(products, G, K, v_0=0):
    return {'graph': G, 'products': products, 'K': K, 'V_pay': V_PAY,
            'v_0': v_0, 'target': 'min_distance'}


# --------------------------------------------------------------------------- #
# Time model
# --------------------------------------------------------------------------- #

def test_time_differs_from_distance(store):
    """The congestion model must make time != distance (else no Pareto front)."""
    _products, G, _nodes = store
    ratios = []
    for (i, j, d) in [(0, 67, 'l'), (67, 83, 'l'), (83, 63, 'l')]:
        import networkx as nx
        p = nx.shortest_path(G, i, j, weight='length')
        dist = sum(G[p[k]][p[k + 1]]['length'] for k in range(len(p) - 1))
        time = sum(G[p[k]][p[k + 1]]['time'] for k in range(len(p) - 1))
        ratios.append(time / dist)
    assert max(ratios) > 1.3, "time should diverge meaningfully from distance"


def test_congestion_contrast():
    core = aisle_congestion((8, 6), (9, 6))     # central core edge
    perimeter = aisle_congestion((1, 6), (1, 7))  # fast outer lane
    assert core > 3 * perimeter


# --------------------------------------------------------------------------- #
# Solver correctness
# --------------------------------------------------------------------------- #

def test_front_is_non_dominated(store):
    products, G, _nodes = store
    res = maco_pareto(_instance(products, G, [1, 7, 20, 35, 50]), MacoParams(seed=1))
    pts = [(r.distance, r.time) for r in res["routes"]]
    for a in pts:
        for b in pts:
            if a is not b:
                assert not _dominates(a, b), f"{a} dominates {b} in the front"


def test_routes_start_and_end_correctly(store):
    products, G, _nodes = store
    res = maco_pareto(_instance(products, G, [3, 9, 24, 38], v_0=0), MacoParams(seed=2))
    for r in res["routes"]:
        assert r.full_path[0] == 0          # starts at source
        assert r.full_path[-1] == V_PAY[0]  # ends at checkout


def test_path_costs_are_consistent(store):
    """Each route's stored (distance, time) must equal its walked path."""
    products, G, _nodes = store
    res = maco_pareto(_instance(products, G, [5, 15, 41, 10, 34]), MacoParams(seed=1))
    for r in res["routes"]:
        d = sum(G[r.full_path[k]][r.full_path[k + 1]]['length']
                for k in range(len(r.full_path) - 1))
        t = sum(G[r.full_path[k]][r.full_path[k + 1]]['time']
                for k in range(len(r.full_path) - 1))
        assert d == pytest.approx(r.distance, abs=1e-6)
        assert t == pytest.approx(r.time, abs=1e-6)


def test_determinism(store):
    products, G, _nodes = store
    inst = _instance(products, G, [1, 7, 20, 35, 50])
    a = [(r.distance, r.time) for r in maco_pareto(inst, MacoParams(seed=7))["routes"]]
    b = [(r.distance, r.time) for r in maco_pareto(inst, MacoParams(seed=7))["routes"]]
    assert a == b


def test_matches_brute_force_front(store):
    """On a small list the solver should recover (almost) the true front."""
    products, G, _nodes = store
    K = [35, 36, 31, 26, 41]
    s, stops, e, idx, _pn = _required_nodes(_instance(products, G, K))

    legs = {(a, b): ([(0., 0., [a])] if a == b else _biobj_paths(G, idx[a], idx[b]))
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
    true_front = prune(glob)

    maco = prune([(r.distance, r.time)
                  for r in maco_pareto(_instance(products, G, K), MacoParams(seed=1))["routes"]])
    # the solver should find the full true front for an instance this small
    assert len(maco) == len(true_front)


def test_drop_in_solver_contract(store):
    """maco_solver must mirror heuristic_solver's 4-tuple shape."""
    products, G, _nodes = store
    K = [1, 7, 20, 35, 50]
    on, pn, ttime, tdist = maco_solver({**_instance(products, G, K), 'target': 'min_time'})
    assert pn == [products[k]['locations'][0] for k in K]
    assert on[-1] == V_PAY[0]
    assert ttime > 0 and tdist > 0


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
