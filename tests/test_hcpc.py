"""HCPC parity tests against R FactoMineR fixtures."""

from __future__ import annotations

import numpy as np
from itertools import combinations

from factominer import HCPC, PCA
from factominer.datasets import load_decathlon


def _adjusted_rand_index(a, b) -> float:
    """Adjusted Rand Index without sklearn dependency."""
    a = np.asarray(a)
    b = np.asarray(b)
    n = a.size
    a_levels = np.unique(a)
    b_levels = np.unique(b)
    contingency = np.zeros((a_levels.size, b_levels.size), dtype=np.int64)
    for i, av in enumerate(a_levels):
        for j, bv in enumerate(b_levels):
            contingency[i, j] = int(((a == av) & (b == bv)).sum())
    sum_comb_c = sum(_comb2(int(x)) for x in contingency.flatten())
    sum_a = sum(_comb2(int(x)) for x in contingency.sum(axis=1))
    sum_b = sum(_comb2(int(x)) for x in contingency.sum(axis=0))
    total = _comb2(n)
    if total == 0:
        return 1.0
    expected = sum_a * sum_b / total
    max_index = (sum_a + sum_b) / 2
    if max_index - expected == 0:
        return 1.0
    return float((sum_comb_c - expected) / (max_index - expected))


def _comb2(k: int) -> int:
    return k * (k - 1) // 2


def test_hcpc_cluster_agreement(r_hcpc_decathlon):
    df = load_decathlon().iloc[:, :10]
    pca = PCA(df, ncp=5)
    res = HCPC(pca, nb_clust=4)
    r_clust = [int(c) for c in r_hcpc_decathlon["clust"]]
    py_clust = res.data_clust["clust"].astype(int).to_list()
    ari = _adjusted_rand_index(r_clust, py_clust)
    assert ari >= 0.999, f"ARI={ari}; HCPC partition disagrees with R FactoMineR"


def test_hcpc_data_clust_has_cluster_column():
    df = load_decathlon().iloc[:, :10]
    pca = PCA(df, ncp=5)
    res = HCPC(pca, nb_clust=3)
    assert "clust" in res.data_clust.columns
    assert res.data_clust["clust"].nunique() == 3


def test_hcpc_auto_select_k():
    df = load_decathlon().iloc[:, :10]
    pca = PCA(df, ncp=5)
    res = HCPC(pca, nb_clust=-1, min=2, max=6)
    k = res.data_clust["clust"].nunique()
    assert 2 <= k <= 6
