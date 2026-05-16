"""Hierarchical Clustering on Principal Components — FactoMineR-compatible API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import pdist

from ._result import Result


@dataclass(frozen=True)
class HCPCResult:
    data_clust: pd.DataFrame
    desc_var: dict[str, Any] = field(default_factory=dict)
    desc_axes: dict[str, Any] = field(default_factory=dict)
    desc_ind: dict[str, Any] = field(default_factory=dict)
    call: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"<factominer.HCPC clusters={self.data_clust['clust'].nunique()}>"


def HCPC(  # noqa: N802 — mirrors R
    res: Result,
    nb_clust: int = -1,
    min: int = 3,  # noqa: A002 — mirrors R kwarg
    max: int = 10,  # noqa: A002
    consol: bool = True,
    iter_max: int = 10,
    metric: str = "euclidean",
    method_clust: str = "ward",
    random_state: int = 0,
) -> HCPCResult:
    """Hierarchical clustering on principal components.

    Mirrors ``FactoMineR::HCPC``. Operates on a PCA / CA / MCA result; uses the
    individuals (or rows) coordinate matrix, builds a Ward-linkage hierarchy,
    cuts at the level with the largest relative loss in within-cluster inertia
    (when ``nb_clust=-1``), then optionally consolidates with k-means.
    """
    coord = _individuals_coord(res)
    n, _ = coord.shape
    if n < 3:
        raise ValueError("HCPC needs at least 3 individuals")
    if metric != "euclidean":
        raise ValueError("only euclidean metric is supported")
    if method_clust not in {"ward", "complete", "average", "single"}:
        raise ValueError(f"unsupported linkage: {method_clust}")

    # Ward.D2 in R == scipy's "ward" with squared euclidean? No: scipy 'ward' implements Ward.D2 by
    # operating on raw euclidean distances. We follow scipy's convention.
    Z = linkage(pdist(coord.to_numpy(), metric="euclidean"), method=method_clust)

    if nb_clust == -1:
        k = _auto_select_k(Z, n, lo=min, hi=max)
    elif nb_clust < 2:
        raise ValueError("nb_clust must be >= 2 or -1 for auto")
    else:
        k = int(nb_clust)

    clusters = fcluster(Z, t=k, criterion="maxclust")

    if consol:
        clusters = _kmeans_consolidate(coord.to_numpy(), clusters, iter_max=iter_max, random_state=random_state)

    # Build data.clust frame: coordinates + cluster column
    data_clust = coord.copy()
    data_clust["clust"] = pd.Categorical(clusters, categories=sorted(set(clusters)))

    desc_axes = _describe_axes(coord, clusters)
    desc_ind = _describe_individuals(coord, clusters)

    return HCPCResult(
        data_clust=data_clust,
        desc_var={},  # populated by callers that pass the raw data
        desc_axes=desc_axes,
        desc_ind=desc_ind,
        call={
            "t": {"linkage": Z, "method": method_clust, "metric": metric},
            "nb_clust": k,
            "min": min,
            "max": max,
            "consol": consol,
            "iter_max": iter_max,
            "n": n,
        },
    )


def _individuals_coord(res: Result) -> pd.DataFrame:
    if res.ind is not None:
        return res.ind.coord
    if res.row is not None:
        return res.row.coord
    raise ValueError("res has no ind/row coordinates")


def _auto_select_k(Z: np.ndarray, n: int, lo: int, hi: int) -> int:
    """Pick k by largest relative within-inertia loss between consecutive cuts."""
    lo = max(2, int(lo))
    hi = min(int(hi), n - 1)
    heights = Z[:, 2]  # length n-1, in increasing order of merges
    inertia_gain = heights[::-1]  # heights[i] in original order = merge i, so gain at k=i+1 is heights[n-2-i]
    # within-inertia after cutting at k clusters = sum of remaining merge heights
    cum = np.cumsum(inertia_gain)
    # ratio of inertia loss going from k to k+1
    best_k, best_ratio = lo, -np.inf
    for k in range(lo, hi + 1):
        if k - 1 >= len(cum) or k >= len(cum):
            continue
        before = cum[k - 1]
        after = cum[k]
        if before <= 0:
            continue
        ratio = (after - before) / before
        if ratio > best_ratio:
            best_ratio = ratio
            best_k = k
    return best_k


def _kmeans_consolidate(
    X: np.ndarray,
    init_clusters: np.ndarray,
    iter_max: int,
    random_state: int,
) -> np.ndarray:
    """K-means refinement using the hierarchical partition's centroids as seeds."""
    rng = np.random.default_rng(random_state)
    labels = init_clusters.copy()
    uniq = np.unique(labels)
    if uniq.size < 2:
        return labels
    centroids = np.vstack([X[labels == c].mean(axis=0) for c in uniq])
    for _ in range(iter_max):
        d2 = ((X[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
        new_labels_idx = np.argmin(d2, axis=1)
        new_labels = uniq[new_labels_idx]
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for ci, c in enumerate(uniq):
            mask = labels == c
            if mask.any():
                centroids[ci] = X[mask].mean(axis=0)
            else:
                # Re-seed an empty cluster with a random point.
                centroids[ci] = X[rng.integers(0, X.shape[0])]
    return labels


def _describe_axes(coord: pd.DataFrame, clusters: np.ndarray) -> dict[str, Any]:
    """v-test of each axis vs each cluster (means standardized under H0)."""
    n = coord.shape[0]
    out: dict[str, Any] = {}
    for c in sorted(np.unique(clusters)):
        mask = clusters == c
        nA = int(mask.sum())
        if nA == 0 or nA == n:
            continue
        mean_A = coord.loc[mask].mean()
        mean_all = coord.mean()
        var_all = coord.var(ddof=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            v = (mean_A - mean_all) / np.sqrt(var_all * (n - nA) / (nA * (n - 1)))
        out[str(c)] = pd.DataFrame({"v.test": v, "Mean.in.category": mean_A, "Overall.mean": mean_all})
    return out


def _describe_individuals(coord: pd.DataFrame, clusters: np.ndarray) -> dict[str, Any]:
    """Per-cluster paragons (closest to centroid) and outliers (farthest)."""
    out: dict[str, Any] = {}
    X = coord.to_numpy()
    for c in sorted(np.unique(clusters)):
        mask = clusters == c
        if not mask.any():
            continue
        Xc = X[mask]
        centroid = Xc.mean(axis=0)
        d_para = np.linalg.norm(Xc - centroid, axis=1)
        order_para = np.argsort(d_para)
        names = list(coord.index[mask])
        out[str(c)] = {
            "para": pd.Series([d_para[i] for i in order_para], index=[names[i] for i in order_para]),
            "dist": pd.Series(d_para, index=names),
        }
    return out
