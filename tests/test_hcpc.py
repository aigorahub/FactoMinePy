"""HCPC parity tests against R FactoMineR fixtures.

R's ``HCPC`` returns ``data.clust`` (original X + ``clust`` column),
``desc.var`` (a ``catdes`` of the cluster column against every other
variable), ``desc.axes`` (per-axis ``condes``), and ``desc.ind``. The
partition is checked via Adjusted Rand Index ≥ 0.999 (k-means
consolidation can swap a couple of labels but the partition is the same);
``desc.var`` is checked column-by-column against R's catdes output now
that our HCPC delegates to the parity-verified ``catdes``.
"""

from __future__ import annotations

import math

import numpy as np

from factominer import HCPC, PCA
from factominer.datasets import load_decathlon


def _adjusted_rand_index(a, b) -> float:
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


def _row_dict_to_map(rows, value_keys):
    out = {}
    if rows is None:
        return out
    for row in rows:
        label = (
            row.get("_row")
            or row.get("rowname")
            or row.get("variable")
        )
        if label is None:
            continue
        out[str(label)] = {k: row.get(k) for k in value_keys}
    return out


def _run_hcpc():
    df = load_decathlon().iloc[:, :10]
    pca = PCA(df, scale_unit=True, ncp=5)
    return HCPC(pca, nb_clust=4)


def test_hcpc_cluster_agreement(r_hcpc_decathlon):
    res = _run_hcpc()
    r_clust = [int(c) for c in r_hcpc_decathlon["clust"]]
    py_clust = res.data_clust["clust"].astype(int).to_list()
    ari = _adjusted_rand_index(r_clust, py_clust)
    assert ari >= 0.999, f"ARI={ari}; HCPC partition disagrees with R FactoMineR"


def test_hcpc_data_clust_has_original_columns(r_hcpc_decathlon):
    """R's ``data.clust`` has the original X columns plus ``clust``. Verify
    we expose the same column layout."""
    res = _run_hcpc()
    r_cols = r_hcpc_decathlon.get("data_clust_columns")
    if not r_cols:
        # Older fixture without columns metadata; check the structure only.
        assert "clust" in res.data_clust.columns
        return
    assert list(res.data_clust.columns) == list(r_cols), (
        f"R cols: {r_cols}, Py cols: {list(res.data_clust.columns)}"
    )


def test_hcpc_data_clust_index(r_hcpc_decathlon):
    res = _run_hcpc()
    r_idx = r_hcpc_decathlon.get("data_clust_index") or []
    if not r_idx:
        return
    assert list(res.data_clust.index) == list(r_idx)


def test_hcpc_desc_var_quanti_var(r_hcpc_decathlon):
    """desc.var$quanti.var = catdes on (X + clust). Eta² and P-value should
    match R to ~1e-9 / 1e-6."""
    res = _run_hcpc()
    r_qv = r_hcpc_decathlon.get("desc.var", {}).get("quanti.var") or []
    if not r_qv:
        return
    r_map = _row_dict_to_map(r_qv, ["Eta2", "P-value"])
    py_qv = res.desc_var.get("quanti_var")
    assert py_qv is not None, "Python HCPC missing desc_var.quanti_var"
    for var, expect in r_map.items():
        assert var in py_qv.index, f"{var} missing"
        assert math.isclose(
            float(expect["Eta2"]), float(py_qv.loc[var, "Eta2"]), abs_tol=1e-9
        ), f"{var} Eta2 R={expect['Eta2']} Py={py_qv.loc[var, 'Eta2']}"
        assert math.isclose(
            float(expect["P-value"]),
            float(py_qv.loc[var, "P-value"]),
            rel_tol=1e-6,
            abs_tol=1e-18,
        )


def test_hcpc_desc_var_quanti_per_level(r_hcpc_decathlon):
    """desc.var$quanti per cluster — same schema as catdes per-level quanti."""
    res = _run_hcpc()
    r_qu = r_hcpc_decathlon.get("desc.var", {}).get("quanti") or {}
    py_qu = res.desc_var.get("quanti") or {}
    if not r_qu:
        return
    for lvl, rows in r_qu.items():
        if not rows:
            assert (py_qu.get(str(lvl)) is None) or py_qu[str(lvl)].empty
            continue
        py_frame = py_qu.get(str(lvl))
        assert py_frame is not None, f"cluster {lvl}: Python missing quanti"
        r_map = _row_dict_to_map(
            rows,
            ["v.test", "Mean in category", "Overall mean", "sd in category",
             "Overall sd", "p.value", "n"],
        )
        for var, expect in r_map.items():
            assert var in py_frame.index, f"cluster {lvl} {var} missing"
            for col, atol in [
                ("Mean in category", 1e-9),
                ("Overall mean", 1e-9),
                ("sd in category", 1e-9),
                ("Overall sd", 1e-9),
                ("v.test", 1e-6),
            ]:
                if expect[col] is None:
                    continue
                assert math.isclose(
                    float(expect[col]), float(py_frame.loc[var, col]), abs_tol=atol
                ), f"cluster {lvl} {var} {col}: R={expect[col]} Py={py_frame.loc[var, col]}"
            assert math.isclose(
                float(expect["p.value"]),
                float(py_frame.loc[var, "p.value"]),
                rel_tol=1e-5,
                abs_tol=1e-18,
            )
            if expect["n"] is not None:
                assert int(py_frame.loc[var, "n"]) == int(expect["n"])


def test_hcpc_auto_select_k():
    df = load_decathlon().iloc[:, :10]
    pca = PCA(df, ncp=5)
    res = HCPC(pca, nb_clust=-1, min=2, max=6)
    k = res.data_clust["clust"].nunique()
    assert 2 <= k <= 6
