"""mACO1 multi-objective solver for the store picking problem.

Adaptation of the validated Python port of mACO1 (Lopez-Ibanez & Stutzle,
2012) to the SONAE picking environment.  The shopper walks an *open path*

        source (v_0)  ->  product node  ->  ...  ->  product node  ->  checkout

minimising two objectives at once: total walked **distance** and total
**time** (distance scaled by aisle congestion, see ``graph.aisle_congestion``).
Rather than returning one route for a single chosen objective, the solver
returns the whole **Pareto front**: routes that do not dominate each other --
for example one that is short but slow (cutting through the congested core) and
one that is longer but faster (detouring via the fast perimeter lanes).

Two sources of trade-off are modelled:
  1. the **order** in which the product nodes are visited, and
  2. the **path taken between two stops** -- between a pair of nodes there can
     be several non-dominated (distance, time) paths (a short congested one and
     a longer clear one).  These per-leg options are what make the front rich.

mACO1 mechanics kept faithful to the C reference / validated port
-----------------------------------------------------------------
  * Two pheromone matrices (one per objective), initialised at tau_max (MMAS).
  * Three weight groups lambda in {0, 0.5, 1}; ants of a group share one
    ``tau_total`` matrix built with RANDOM per-row pheromone aggregation and a
    weighted-sum heuristic ``(1-lambda)*heu1 + lambda*heu2``, ``heu = 1/(c+0.1)``.
  * MMAS trail limits ``tau_max = 1/rho``, ``tau_min = tau_max/(2*M)`` with
    clamping after every update; mixed best-so-far schedule
    (INT_MAX -> 25 -> 5 -> 3 -> 2 -> 1); constant ``d_tau = 1`` deposit.

The ACO searches over visiting orders; for every order constructed the exact
non-dominated set of its concrete walks (the Minkowski front of the per-leg
options) is extracted and merged into a global archive, so the returned front
is both rich and made of real, drawable routes.
"""

from __future__ import annotations

import dataclasses
import heapq
import time
from typing import Optional

import networkx as nx
import numpy as np

_WEIGHTS = np.array([0.0, 0.5, 1.0])
_NUM_WEIGHTS = 3
_FRONT_CAP = 60          # safety cap on a running Minkowski front
_ROUND = 3               # decimals used for dominance / dedup


# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class MacoParams:
    """Hyperparameters for an mACO1 run (store-sized defaults)."""
    num_ants: int = 60
    alpha: float = 1.0
    beta: float = 2.0
    rho: float = 0.02
    max_iter: int = 150
    time_limit: float = 2.5   # wall-clock budget; keeps the UI responsive
    seed: int = 1


@dataclasses.dataclass
class ParetoRoute:
    """One non-dominated route returned by the solver."""
    stop_order: list      # visiting order of the (unique) product nodes
    ordered_nodes: list   # [v_0?] + stop_order + [v_end], heuristic-solver shape
    full_path: list       # full node-by-node walk actually taken (for drawing)
    distance: float
    time: float


# ---------------------------------------------------------------------------
# Dominance helpers
# ---------------------------------------------------------------------------

def _dominates(a, b) -> bool:
    return (a[0] <= b[0] and a[1] <= b[1]) and (a[0] < b[0] or a[1] < b[1])


def _prune_paths(items):
    """Keep the non-dominated subset of (d, t, path) tuples (minimisation)."""
    items = sorted(items, key=lambda it: (round(it[0], _ROUND), round(it[1], _ROUND)))
    front = []
    seen = set()
    for d, t, path in items:
        key = (round(d, _ROUND), round(t, _ROUND))
        if key in seen:
            continue
        dominated = False
        for fd, ft, _fp in front:
            if _dominates((fd, ft), (d, t)):
                dominated = True
                break
        if dominated:
            continue
        front = [(fd, ft, fp) for (fd, ft, fp) in front
                 if not _dominates((d, t), (fd, ft))]
        front.append((d, t, path))
        seen = {(round(x[0], _ROUND), round(x[1], _ROUND)) for x in front}
    return front


# ---------------------------------------------------------------------------
# Per-leg bi-objective shortest paths
# ---------------------------------------------------------------------------

def _biobj_paths(G, s, t):
    """Non-dominated (distance, time, path) options between two nodes.

    Label-setting (multi-objective Dijkstra) over the store grid.  Returns the
    Pareto set of paths; on this small grid each leg has only a handful.
    """
    labels = {n: [] for n in G.nodes()}
    labels[s] = [(0.0, 0.0, (s,))]
    pq = [(0.0, 0.0, s, (s,))]
    while pq:
        d, tm, u, path = heapq.heappop(pq)
        # skip stale labels
        if not any(abs(ld - d) < 1e-12 and abs(lt - tm) < 1e-12
                   for (ld, lt, _p) in labels[u]):
            continue
        for v in G.neighbors(u):
            if v in path:                      # simple paths only
                continue
            nd = d + G[u][v]['length']
            nt = tm + G[u][v]['time']
            cand = (nd, nt)
            lab = labels[v]
            if any(_dominates((ld, lt), cand) or (ld == nd and lt == nt)
                   for (ld, lt, _p) in lab):
                continue
            npath = path + (v,)
            labels[v] = [(ld, lt, p) for (ld, lt, p) in lab
                         if not _dominates(cand, (ld, lt))]
            labels[v].append((nd, nt, npath))
            heapq.heappush(pq, (nd, nt, v, npath))
    return [(d, t, list(p)) for (d, t, p) in _prune_paths(
        [(d, t, list(p)) for (d, t, p) in labels[t]])]


# ---------------------------------------------------------------------------
# Instance preprocessing
# ---------------------------------------------------------------------------

def _required_nodes(instance):
    """(source_idx, stop_indices, end_idx, index_nodes, product_nodes)."""
    products = instance['products']
    K = instance['K']
    v_0 = instance['v_0']
    v_end = instance['V_pay'][0]

    product_nodes = [products[k]['locations'][0] for k in K]
    stops = []
    for n in product_nodes:
        if n not in stops and n != v_0 and n != v_end:
            stops.append(n)
    index_nodes = [v_0] + stops + [v_end]
    return 0, list(range(1, 1 + len(stops))), len(index_nodes) - 1, index_nodes, product_nodes


def _build_legs(G, index_nodes):
    """legs[(i, j)] = list of (distance, time, path_nodes) for index pair."""
    legs = {}
    for a, na in enumerate(index_nodes):
        for b, nb in enumerate(index_nodes):
            if a == b:
                legs[(a, b)] = [(0.0, 0.0, [na])]
            elif (b, a) in legs:                     # reuse reversed path
                legs[(a, b)] = [(d, t, list(reversed(p)))
                                for (d, t, p) in legs[(b, a)]]
            else:
                legs[(a, b)] = _biobj_paths(G, na, nb)
    return legs


def _scalar_leg_cost(legs, a, b, lam):
    """Best weighted-sum cost of leg (a, b) under weight lambda."""
    return min((1.0 - lam) * d + lam * t for (d, t, _p) in legs[(a, b)])


# ---------------------------------------------------------------------------
# mACO1 mechanics (mirrors aco.py from the validated port)
# ---------------------------------------------------------------------------

def _build_tau_total(ph1, ph2, heu1, heu2, lam, alpha, beta, rng):
    m = ph1.shape[0]
    if lam == 0.0:
        ph_chosen = ph1
    elif lam == 1.0:
        ph_chosen = ph2
    else:
        use_ph2 = rng.random(m) < lam
        ph_chosen = np.where(use_ph2[:, None], ph2, ph1)
    heu_combined = (1.0 - lam) * heu1 + lam * heu2
    return np.power(ph_chosen, alpha) * np.power(heu_combined, beta)


def _construct_order(tau_total, source_idx, stop_indices, rng):
    order = []
    remaining = list(stop_indices)
    current = source_idx
    while remaining:
        w = np.array([tau_total[current, s] for s in remaining])
        tot = w.sum()
        if tot <= 0.0:
            nxt = remaining[int(rng.integers(0, len(remaining)))]
        else:
            nxt = remaining[int(rng.choice(len(remaining), p=w / tot))]
        order.append(nxt)
        remaining.remove(nxt)
        current = nxt
    return order


def _order_front(order, source_idx, end_idx, legs, index_nodes):
    """Exact non-dominated set of concrete walks for a fixed visiting order."""
    seq = [source_idx] + order + [end_idx]
    cur = [(0.0, 0.0, [index_nodes[source_idx]])]
    for k in range(len(seq) - 1):
        opts = legs[(seq[k], seq[k + 1])]
        nxt = []
        for (cd, ct, cpath) in cur:
            for (ld, lt, lpath) in opts:
                nxt.append((cd + ld, ct + lt, cpath + lpath[1:]))
        cur = _prune_paths(nxt)
        if len(cur) > _FRONT_CAP:               # keep extremes + spread
            cur.sort(key=lambda it: it[0])
            step = len(cur) / _FRONT_CAP
            cur = [cur[int(i * step)] for i in range(_FRONT_CAP)]
    return cur


def _deposit(ph, order, source_idx, end_idx, d_tau=1.0):
    seq = [source_idx] + order + [end_idx]
    for k in range(len(seq) - 1):
        i, j = seq[k], seq[k + 1]
        ph[i, j] += d_tau
        ph[j, i] = ph[i, j]


def _mmas_use_best_so_far(iteration, bf_freq):
    use_bsf = (iteration % bf_freq[0]) == 0
    if iteration < 25:
        bf_freq[0] = 25
    elif iteration < 75:
        bf_freq[0] = 5
    elif iteration < 125:
        bf_freq[0] = 3
    elif iteration < 250:
        bf_freq[0] = 2
    else:
        bf_freq[0] = 1
    return use_bsf


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------

def maco_pareto(instance, params: Optional[MacoParams] = None):
    """Run mACO1 and return the Pareto front of routes for ``instance``."""
    if params is None:
        params = MacoParams()

    source_idx, stop_indices, end_idx, index_nodes, product_nodes = _required_nodes(instance)
    G = instance['graph']
    v_0 = instance['v_0']
    v_end = instance['V_pay'][0]

    legs = _build_legs(G, index_nodes)
    start = time.perf_counter()

    # Global archive of non-dominated concrete routes.
    global_front: list = []   # (d, t, full_path, stop_order_nodes)

    def add_route(d, t, full_path, order):
        nonlocal global_front
        key = (round(d, _ROUND), round(t, _ROUND))
        for (gd, gt, _fp, _o) in global_front:
            if _dominates((gd, gt), (d, t)) or (round(gd, _ROUND), round(gt, _ROUND)) == key:
                return
        global_front = [g for g in global_front
                        if not _dominates((d, t), (g[0], g[1]))]
        stop_nodes = [index_nodes[i] for i in order]
        global_front.append((d, t, full_path, stop_nodes))

    # Trivial: zero or one stop -> just take that order's front, no search.
    if len(stop_indices) <= 1:
        for (d, t, path) in _order_front(list(stop_indices), source_idx, end_idx, legs, index_nodes):
            add_route(d, t, path, list(stop_indices))
        return _finalise(global_front, v_0, v_end, 0, 0.0, len(stop_indices))

    rng = np.random.default_rng(params.seed)
    m = len(index_nodes)

    # Heuristic matrices use the best achievable leg cost per objective.
    heu1 = np.full((m, m), 1.0)   # distance objective (lambda = 0)
    heu2 = np.full((m, m), 1.0)   # time objective (lambda = 1)
    for a in range(m):
        for b in range(m):
            if a == b:
                continue
            heu1[a, b] = 1.0 / (_scalar_leg_cost(legs, a, b, 0.0) + 0.1)
            heu2[a, b] = 1.0 / (_scalar_leg_cost(legs, a, b, 1.0) + 0.1)

    tau_max = 1.0 / params.rho
    tau_min = tau_max / (2.0 * m)
    ph1 = np.full((m, m), tau_max)
    ph2 = np.full((m, m), tau_max)
    ants_per_weight = max(1, params.num_ants // _NUM_WEIGHTS)

    bsf1_order = [None] * _NUM_WEIGHTS
    bsf2_order = [None] * _NUM_WEIGHTS
    bsf1_val = [np.inf] * _NUM_WEIGHTS
    bsf2_val = [np.inf] * _NUM_WEIGHTS
    bf_freq = [2 ** 31]
    n_iter = 0

    for iteration in range(1, params.max_iter + 1):
        n_iter = iteration
        ib1_order = [None] * _NUM_WEIGHTS
        ib2_order = [None] * _NUM_WEIGHTS
        ib1_val = [np.inf] * _NUM_WEIGHTS
        ib2_val = [np.inf] * _NUM_WEIGHTS

        for w_idx, lam in enumerate(_WEIGHTS):
            tau_total = _build_tau_total(ph1, ph2, heu1, heu2, float(lam),
                                         params.alpha, params.beta, rng)
            for _ in range(ants_per_weight):
                order = _construct_order(tau_total, source_idx, stop_indices, rng)

                # Exact non-dominated walks for this order -> archive them all.
                front = _order_front(order, source_idx, end_idx, legs, index_nodes)
                for (d, t, path) in front:
                    add_route(d, t, path, order)

                # Scalarised totals drive the per-weight best tracking.
                d_scalar = min((1.0 - lam) * d + lam * t for (d, t, _p) in front)
                # distance- and time-extreme values for SELECT_BY_WEIGHT
                d_best = min(d for (d, t, _p) in front)
                t_best = min(t for (d, t, _p) in front)
                if d_best < ib1_val[w_idx]:
                    ib1_order[w_idx] = order; ib1_val[w_idx] = d_best
                if t_best < ib2_val[w_idx]:
                    ib2_order[w_idx] = order; ib2_val[w_idx] = t_best
                if d_best < bsf1_val[w_idx]:
                    bsf1_order[w_idx] = list(order); bsf1_val[w_idx] = d_best
                if t_best < bsf2_val[w_idx]:
                    bsf2_order[w_idx] = list(order); bsf2_val[w_idx] = t_best

        ph1 *= 1.0 - params.rho
        ph2 *= 1.0 - params.rho
        use_bsf = _mmas_use_best_so_far(iteration, bf_freq)
        src1 = bsf1_order if use_bsf else ib1_order
        src2 = bsf2_order if use_bsf else ib2_order
        if src1[0] is not None: _deposit(ph1, src1[0], source_idx, end_idx)
        if src2[2] is not None: _deposit(ph2, src2[2], source_idx, end_idx)
        if src1[1] is not None: _deposit(ph1, src1[1], source_idx, end_idx)
        if src2[1] is not None: _deposit(ph2, src2[1], source_idx, end_idx)
        np.clip(ph1, tau_min, tau_max, out=ph1)
        np.clip(ph2, tau_min, tau_max, out=ph2)

        if (time.perf_counter() - start) >= params.time_limit:
            break

    return _finalise(global_front, v_0, v_end, n_iter,
                     time.perf_counter() - start, len(stop_indices))


def _finalise(global_front, v_0, v_end, n_iter, elapsed, n_stops):
    routes = []
    for (d, t, full_path, stop_nodes) in global_front:
        routes.append(ParetoRoute(
            stop_order=stop_nodes,
            ordered_nodes=_ordered_nodes(v_0, stop_nodes, v_end),
            full_path=full_path,
            distance=float(d),
            time=float(t),
        ))
    routes.sort(key=lambda r: (r.distance, r.time))
    return {"routes": routes, "n_iter": n_iter, "elapsed": elapsed, "n_stops": n_stops}


def _ordered_nodes(v_0, stop_order_nodes, v_end):
    if v_0 in stop_order_nodes:
        ordered = list(stop_order_nodes)
    else:
        ordered = [v_0] + list(stop_order_nodes)
    ordered.append(v_end)
    return ordered


def maco_solver(instance):
    """Drop-in replacement for ``heuristic_solver`` (single representative).

    Returns ``ordered_nodes, product_nodes, total_time, total_distance`` for the
    Pareto route that best matches ``instance['target']``.
    """
    result = maco_pareto(instance)
    routes = result["routes"]
    _s, _st, _e, _idx, product_nodes = _required_nodes(instance)
    target = instance.get('target', 'min_distance')
    best = (min(routes, key=lambda r: r.time) if target == 'min_time'
            else min(routes, key=lambda r: r.distance))
    return best.ordered_nodes, product_nodes, best.time, best.distance
