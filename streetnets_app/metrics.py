"""Network metrics for StreetNets' Deep Analysis mode.

All heavy computation lives here, Streamlit-free (pattern of ``data.py``), so
it can be reused from scripts, tests, and a future CLI. The Streamlit page
wraps these calls with session-state caching and progress UI.

Methodology notes (matching the 18-city database in examples_stats.csv):

- The database graphs were built with ``ox.graph_from_point(dist=4000,
  network_type="drive", truncate_by_edge=True)`` reduced to the largest
  strongly connected component.
- "Edge Betweenness" was computed as ``nx.edge_betweenness_centrality(G,
  weight="length")`` — directed NetworkX normalization (÷ n·(n−1)), keyed by
  (u, v) and broadcast to parallel (u, v, key) edges.
- Alpha/Beta/Gamma are the Kansky indices (validated exactly against the CSV).
- The remaining columns come from ``ox.basic_stats(G, area=(2*4000)**2)``.

The heavy centralities run on python-igraph (C core) for speed, with results
normalized to match the NetworkX conventions above. Point-to-point routing and
limited single-source sweeps instead use the shared ``scipy.sparse.csgraph``
Dijkstra core in ``csr_paths`` (the faster path for that workload).
"""

from __future__ import annotations

from dataclasses import dataclass

import igraph as ig
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
import geopandas as gpd

# Column order of examples_stats.csv (after the index city name)
STATS_COLUMNS = [
    "n", "m", "k_avg", "edge_length_total", "edge_length_avg",
    "streets_per_node_avg", "intersection_count", "street_length_total",
    "street_segment_count", "street_length_avg", "circuity_avg",
    "self_loop_proportion", "node_density_km", "intersection_density_km",
    "edge_density_km", "street_density_km", "PageRank Max", "PageRank Min",
    "Alpha", "Beta", "Gamma",
]


# ---------------------------------------------------------------------------
# Graph construction / conversion
# ---------------------------------------------------------------------------

def graph_from_city_gdfs(nodes: gpd.GeoDataFrame, edges: gpd.GeoDataFrame) -> nx.MultiDiGraph:
    """Rebuild an OSMnx MultiDiGraph from the stored database GeoDataFrames.

    The parquet/CSV files carry ``osmid`` and ``(u, v, key)`` as plain columns
    (RangeIndex), and no graph-level CRS — both must be restored before
    ``ox.graph_from_gdfs`` will accept them.
    """
    if not isinstance(nodes.index, pd.MultiIndex) and nodes.index.name != "osmid":
        if "osmid" in nodes.columns:
            nodes = nodes.set_index("osmid")
    if not isinstance(edges.index, pd.MultiIndex):
        edges = edges.set_index(["u", "v", "key"])
    return ox.graph_from_gdfs(nodes, edges, graph_attrs={"crs": "epsg:4326"})


def largest_scc(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """Subgraph copy of the largest strongly connected component.

    Matches the methodology used to build the 18-city database.
    """
    scc = max(nx.strongly_connected_components(G), key=len)
    return G.subgraph(scc).copy()


@dataclass
class IGraphBundle:
    """An igraph copy of a NetworkX graph with index mappings back to it."""

    g: ig.Graph
    node_ids: list            # igraph vertex i  <->  node_ids[i] (osmid)
    edge_keys: list           # igraph edge i    <->  edge_keys[i] ((u, v) or (u, v, key))
    weights: list[float]


def to_igraph(G: nx.MultiDiGraph, weight: str = "length", collapse_parallel: bool = True) -> IGraphBundle:
    """Deterministic manual conversion of a NetworkX (Multi)DiGraph to igraph.

    With ``collapse_parallel=True`` parallel (u, v) edges are collapsed to the
    minimum weight — exactly what NetworkX's Dijkstra does implicitly on
    multigraphs, and how the database's per-edge betweenness was produced.
    ``edge_keys`` then holds (u, v) pairs; otherwise (u, v, key) triples.
    """
    node_ids = list(G.nodes)
    index = {v: i for i, v in enumerate(node_ids)}

    if collapse_parallel:
        best: dict[tuple, float] = {}
        for u, v, data in G.edges(data=True):
            w = float(data.get(weight, 1.0))
            key = (u, v)
            if key not in best or w < best[key]:
                best[key] = w
        edge_keys = list(best.keys())
        weights = [best[k] for k in edge_keys]
        pairs = [(index[u], index[v]) for u, v in edge_keys]
    else:
        edge_keys, weights, pairs = [], [], []
        for u, v, k, data in G.edges(keys=True, data=True):
            edge_keys.append((u, v, k))
            weights.append(float(data.get(weight, 1.0)))
            pairs.append((index[u], index[v]))

    g = ig.Graph(n=len(node_ids), edges=pairs, directed=G.is_directed())
    return IGraphBundle(g=g, node_ids=node_ids, edge_keys=edge_keys, weights=weights)


# ---------------------------------------------------------------------------
# Centrality
# ---------------------------------------------------------------------------

def edge_betweenness(G: nx.MultiDiGraph, weight: str = "length") -> pd.Series:
    """Length-weighted edge betweenness matching the database methodology.

    Equivalent to ``nx.edge_betweenness_centrality(G, weight="length")``:
    parallel edges collapsed to min length, igraph raw counts normalized by
    1/(n·(n−1)) (directed), and the (u, v) value broadcast to every parallel
    (u, v, key) edge. Returns a Series indexed like ``ox.graph_to_gdfs`` edges.
    """
    bundle = to_igraph(G, weight=weight, collapse_parallel=True)
    raw = bundle.g.edge_betweenness(directed=True, weights=bundle.weights)
    n = bundle.g.vcount()
    scale = 1.0 / (n * (n - 1)) if n > 1 else 0.0
    by_pair = {pair: val * scale for pair, val in zip(bundle.edge_keys, raw)}
    idx = list(G.edges(keys=True))
    values = [by_pair[(u, v)] for u, v, _ in idx]
    return pd.Series(values, index=pd.MultiIndex.from_tuples(idx, names=["u", "v", "key"]),
                     name="Edge Betweenness")


def closeness(G: nx.MultiDiGraph, weight: str = "length") -> pd.Series:
    """Length-weighted closeness centrality (incoming distances).

    On a strongly connected graph this equals
    ``nx.closeness_centrality(G, distance="length")`` exactly. On disconnected
    graphs igraph omits NetworkX's reachable-fraction scaling, so compute this
    on the largest SCC (the page's default) for well-defined values.

    Kept on igraph's dedicated C closeness routine: it is faster than the
    all-pairs distance work the ``csr_paths`` Dijkstra core would need for this
    metric (that core is the faster path for point-to-point routing instead).
    """
    bundle = to_igraph(G, weight=weight, collapse_parallel=True)
    vals = bundle.g.closeness(mode="in", weights=bundle.weights, normalized=True)
    return pd.Series(vals, index=pd.Index(bundle.node_ids, name="osmid"), name="closeness")


def pagerank_minmax(G: nx.MultiDiGraph) -> tuple[float, float]:
    """(max, min) of ``nx.pagerank`` with default parameters.

    Deliberately kept on NetworkX so values match the database columns —
    igraph's PRPACK implementation is not numerically identical.
    """
    pr = nx.pagerank(G)
    values = list(pr.values())
    return max(values), min(values)


def kansky_indices(n: int, m: int) -> dict[str, float]:
    """Kansky connectivity indices, formulas validated against the database."""
    return {
        "Alpha": (m - n + 1) / (2 * n - 5),
        "Beta": m / n,
        "Gamma": m / (3 * (n - 2)),
    }


# ---------------------------------------------------------------------------
# Orientation
# ---------------------------------------------------------------------------

def orientation_entropy_stats(G: nx.MultiDiGraph) -> tuple[float, nx.MultiGraph]:
    """Shannon entropy of street bearings, plus the undirected bearing graph.

    The returned graph can be passed to ``ox.plot.plot_orientation`` for the
    polar "compass" histogram.
    """
    Gb = ox.bearing.add_edge_bearings(G)
    Gu = ox.convert.to_undirected(Gb)
    return ox.bearing.orientation_entropy(Gu), Gu


# ---------------------------------------------------------------------------
# Database-comparable stats
# ---------------------------------------------------------------------------

def stats_row(G: nx.MultiDiGraph, area_m2: float) -> pd.Series:
    """One row with the same columns (and order) as examples_stats.csv."""
    basic = ox.stats.basic_stats(G, area=area_m2)
    pr_max, pr_min = pagerank_minmax(G)
    kansky = kansky_indices(basic["n"], basic["m"])
    row = {
        **{k: v for k, v in basic.items() if np.isscalar(v)},
        "PageRank Max": pr_max,
        "PageRank Min": pr_min,
        **kansky,
    }
    return pd.Series({c: row.get(c, np.nan) for c in STATS_COLUMNS})


def percentile_table(row: pd.Series, stats_df: pd.DataFrame) -> pd.DataFrame:
    """Compare one stats row against the database distribution per metric."""
    from scipy.stats import percentileofscore

    records = []
    for col in stats_df.columns:
        if col not in row.index or pd.isna(row[col]):
            continue
        db = stats_df[col].dropna()
        records.append({
            "Metric": col,
            "Your area": row[col],
            "DB min": db.min(),
            "DB median": db.median(),
            "DB max": db.max(),
            "Percentile": percentileofscore(db, row[col], kind="mean"),
        })
    return pd.DataFrame(records).set_index("Metric")


# ---------------------------------------------------------------------------
# Vulnerability
# ---------------------------------------------------------------------------

@dataclass
class DisruptionResult:
    removed_mask: pd.Series          # bool, aligned with the edges GDF index
    before: dict                     # n_weak, n_strong, giant_frac, street_length_m
    after: dict
    removed_length_m: float
    unreachable_fraction: float      # nodes that left the giant weak component
    node_component: pd.Series        # node id -> weak-component label after removal


def _component_stats(g: ig.Graph, total_nodes: int) -> dict:
    weak = g.connected_components(mode="weak")
    strong = g.connected_components(mode="strong")
    giant = max(weak.sizes()) if len(weak) else 0
    return {
        "n_weak": len(weak),
        "n_strong": len(strong),
        "giant_frac": giant / total_nodes if total_nodes else 0.0,
    }


def polygon_disruption(G: nx.MultiDiGraph, edges: gpd.GeoDataFrame,
                       polygon) -> DisruptionResult:
    """Simulate blocking every street segment that intersects ``polygon``.

    ``edges`` must be the ``ox.graph_to_gdfs`` frame of ``G`` (same (u, v, key)
    index). Reports connectivity before/after on the igraph copy.
    """
    hit_pos = edges.sindex.query(polygon, predicate="intersects")
    removed_mask = pd.Series(False, index=edges.index)
    removed_mask.iloc[hit_pos] = True

    bundle = to_igraph(G, collapse_parallel=False)
    total_nodes = bundle.g.vcount()
    before = _component_stats(bundle.g, total_nodes)
    before["street_length_m"] = float(edges["length"].sum())

    removed_keys = set(edges.index[removed_mask])
    eids = [i for i, key in enumerate(bundle.edge_keys) if key in removed_keys]
    g_after = bundle.g.copy()
    g_after.delete_edges(eids)

    after = _component_stats(g_after, total_nodes)
    after["street_length_m"] = float(edges.loc[~removed_mask, "length"].sum())

    membership = g_after.connected_components(mode="weak").membership
    node_component = pd.Series(membership, index=pd.Index(bundle.node_ids, name="osmid"),
                               name="component")
    # Nodes no longer in the (new) giant component, relative to all nodes
    if total_nodes:
        giant_label = node_component.value_counts().idxmax()
        unreachable = float((node_component != giant_label).mean())
    else:
        unreachable = 0.0

    return DisruptionResult(
        removed_mask=removed_mask,
        before=before,
        after=after,
        removed_length_m=float(edges.loc[removed_mask, "length"].sum()),
        unreachable_fraction=unreachable,
        node_component=node_component,
    )


def robustness_curve(G: nx.MultiDiGraph, *, ranking: pd.Series | None = None,
                     fractions: np.ndarray | None = None,
                     strategy: str = "betweenness",
                     seed: int = 0) -> pd.DataFrame:
    """Percolation curve: giant weak-component fraction vs edges removed.

    ``strategy="betweenness"`` removes edges from most to least central using
    ``ranking`` (a Series indexed by (u, v, key); computed here if omitted).
    ``strategy="random"`` shuffles the removal order with ``seed``. Removal is
    cumulative on a single igraph working copy — the ranking is *not*
    recomputed between steps (static-attack convention).
    """
    if fractions is None:
        fractions = np.linspace(0.0, 0.5, 26)

    bundle = to_igraph(G, collapse_parallel=False)
    total_nodes = bundle.g.vcount()
    m = len(bundle.edge_keys)

    if strategy == "betweenness":
        if ranking is None:
            ranking = edge_betweenness(G)
        order = np.argsort([-ranking.get(key, 0.0) for key in bundle.edge_keys])
    elif strategy == "random":
        rng = np.random.default_rng(seed)
        order = rng.permutation(m)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    g = bundle.g.copy()
    # igraph edge ids shift after deletion; delete in descending planned order
    # by tracking original ids via an attribute instead.
    g.es["orig"] = list(range(m))
    removed = 0
    rows = []
    for frac in np.sort(fractions):
        target = int(round(frac * m))
        if target > removed:
            to_remove = set(order[removed:target].tolist())
            eids = [e.index for e in g.es if e["orig"] in to_remove]
            g.delete_edges(eids)
            removed = target
        weak = g.connected_components(mode="weak")
        giant = max(weak.sizes()) if len(weak) else 0
        rows.append({
            "fraction_removed": removed / m if m else 0.0,
            "giant_component_fraction": giant / total_nodes if total_nodes else 0.0,
            "strategy": strategy,
        })
    return pd.DataFrame(rows)
