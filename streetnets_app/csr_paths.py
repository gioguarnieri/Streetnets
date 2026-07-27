"""Optimized shortest-path core for street networks.

Ported from the ``many-paths`` project's ``CSRCore`` (``catchment_index.py``):
the directed graph is held as a ``scipy.sparse`` CSR matrix and all
shortest-path work runs on ``scipy.sparse.csgraph``'s C Dijkstra — no per-edge
Python callbacks, a native distance cutoff via ``limit``, and reusable
single-source sweeps. On street-network workloads (many limited single-source
sweeps and point-to-point queries under temporary edge closures) this was
benchmarked 4-15x faster than the tuned pure-Python A*/NetworkX paths and the
igraph/rustworkx alternatives.

Parallel edges ``(u, v, *)`` collapse to one CSR entry whose weight is the
minimum length among the *currently open* parallels — exactly what NetworkX's
Dijkstra does implicitly on multigraphs, and the same collapse the database's
metrics used. ``close``/``reopen`` maintain that invariant so pathfinding
semantics match the ``MultiDiGraph`` with per-key edge removals.

This is the app's shortest-path engine for point-to-point routing and limited
single-source sweeps — the workload it wins on, and the core of the many-paths
catchment vulnerability index. It is deliberately *not* used for the
centralities: closeness is all-pairs distance work that igraph's dedicated C
routine does faster, and betweenness is shortest-path *counting* (Brandes),
which csgraph's single-predecessor Dijkstra cannot reproduce at all.
"""

from __future__ import annotations

from bisect import insort

import networkx as nx
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra as sp_dijkstra


class CSRCore:
    """Directed street graph as a CSR matrix for ``scipy.sparse.csgraph``.

    Parallel edges ``(u, v, *)`` collapse to one entry whose weight is the
    minimum length among the *currently open* parallels; ``close``/``reopen``
    maintain that invariant, so pathfinding semantics match the
    ``MultiDiGraph`` with per-key removals. The reverse matrix is built once
    for reverse sweeps (catchments) and is only valid on the intact graph.
    """

    def __init__(self, G: nx.MultiDiGraph, weight: str = "length"):
        self.nodes = sorted(G.nodes)
        self.idx = {n: i for i, n in enumerate(self.nodes)}
        n = len(self.nodes)

        lengths: dict[tuple[int, int], list[float]] = {}
        for u, v, d in G.edges(data=True):
            key = (self.idx[u], self.idx[v])
            lengths.setdefault(key, []).append(float(d[weight]))
        rows = np.fromiter((k[0] for k in lengths), dtype=np.int32, count=len(lengths))
        cols = np.fromiter((k[1] for k in lengths), dtype=np.int32, count=len(lengths))
        data = np.fromiter((min(v) for v in lengths.values()),
                           dtype=np.float64, count=len(lengths))
        self.A = csr_matrix((data, (rows, cols)), shape=(n, n))
        self.A_rev = self.A.transpose().tocsr()

        # slot of each collapsed edge in A.data + its open parallel lengths
        self.pos: dict[tuple[int, int], int] = {}
        indptr, indices = self.A.indptr, self.A.indices
        for ui in range(n):
            for j in range(indptr[ui], indptr[ui + 1]):
                self.pos[(ui, int(indices[j]))] = j
        self.avail: dict[int, list[float]] = {}
        for key, ls in lengths.items():
            self.avail[self.pos[key]] = sorted(ls)

    def sweep(self, source, cutoff=np.inf, reverse=False) -> np.ndarray:
        """Single-source shortest-path distances (inf beyond ``cutoff``).

        ``source`` may be one vertex index or an array of them; the result is
        then one row per source. ``reverse=True`` sweeps incoming distances.
        """
        M = self.A_rev if reverse else self.A
        return sp_dijkstra(M, indices=source, limit=cutoff, directed=True)

    def query(self, source, target, budget):
        """Shortest path within ``budget`` as ``(dist, [node indices])`` or None."""
        dist, pred = sp_dijkstra(self.A, indices=source,
                                 limit=np.nextafter(budget, np.inf),
                                 directed=True, return_predecessors=True)
        dv = dist[target]
        if not np.isfinite(dv) or dv > budget:
            return None
        path = [target]
        while path[-1] != source:
            path.append(int(pred[path[-1]]))
        path.reverse()
        return float(dv), path

    def close(self, ui, vi, length):
        """Close one parallel of ``(ui, vi)``; returns an undo token."""
        j = self.pos[(ui, vi)]
        self.avail[j].remove(length)
        self.A.data[j] = self.avail[j][0] if self.avail[j] else np.inf
        return j, length

    def close_min(self, ui, vi):
        """Close the currently cheapest parallel of ``(ui, vi)``."""
        j = self.pos[(ui, vi)]
        return self.close(ui, vi, self.avail[j][0])

    def reopen(self, j, length):
        insort(self.avail[j], length)
        self.A.data[j] = self.avail[j][0]
