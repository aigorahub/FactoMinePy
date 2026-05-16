"""CA parity tests against R FactoMineR fixtures.

Covers every output channel R FactoMineR's ``CA()`` emits: ``eig``,
``svd$vs``, the active row/col blocks (``coord``, ``cos2``, ``contrib``,
``inertia``), and the supplementary blocks (``row.sup`` / ``col.sup``
``coord`` and ``cos2``).
"""

from __future__ import annotations

import numpy as np

from factominer import CA
from factominer._sign import align_to_reference
from factominer.datasets import load_children


def _r_block_to_array(payload, ncp: int) -> tuple[np.ndarray, list[str]]:
    rows, labels = [], []
    for row in payload:
        labels.append(row.get("_row") or row.get("rowname"))
        rows.append(
            [row.get(f"Dim {i + 1}", row.get(f"Dim.{i + 1}")) for i in range(ncp)]
        )
    return np.asarray(rows, dtype=np.float64), labels


# ---------------------------------------------------------------------------
# Plain CA on children[1:14, 1:5]
# ---------------------------------------------------------------------------


def _ca_plain():
    return CA(load_children().iloc[:14, :5], ncp=4)


def test_ca_plain_eigenvalues(r_ca_children_plain):
    res = _ca_plain()
    r_eig = np.array([row["eigenvalue"] for row in r_ca_children_plain["eig"]])
    py_eig = res.eig["eigenvalue"].to_numpy()
    assert py_eig.size == r_eig.size, f"{py_eig.size} vs {r_eig.size}"
    assert np.allclose(py_eig, r_eig, atol=1e-10, rtol=0)


def test_ca_plain_eig_percentages(r_ca_children_plain):
    res = _ca_plain()
    r_pct = np.array([row["percentage of variance"] for row in r_ca_children_plain["eig"]])
    r_cum = np.array(
        [row["cumulative percentage of variance"] for row in r_ca_children_plain["eig"]]
    )
    assert np.allclose(res.eig["percentage of variance"].to_numpy(), r_pct, atol=1e-8)
    assert np.allclose(res.eig["cumulative percentage of variance"].to_numpy(), r_cum, atol=1e-8)


def test_ca_plain_svd_vs(r_ca_children_plain):
    res = _ca_plain()
    r_vs = np.asarray(r_ca_children_plain["svd"]["vs"], dtype=np.float64)
    py_vs = res.svd.vs
    n_real = int(np.sum(np.abs(r_vs) > 1e-12))
    assert np.allclose(py_vs[:n_real], r_vs[:n_real], atol=1e-9, rtol=0)


def test_ca_plain_row_coord(r_ca_children_plain):
    res = _ca_plain()
    r_arr, r_labels = _r_block_to_array(r_ca_children_plain["row"]["coord"], 4)
    py = res.row.coord.loc[r_labels].to_numpy()[:, :4]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_ca_plain_row_cos2(r_ca_children_plain):
    res = _ca_plain()
    r_arr, r_labels = _r_block_to_array(r_ca_children_plain["row"]["cos2"], 4)
    py = res.row.cos2.loc[r_labels].to_numpy()[:, :4]
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_ca_plain_row_contrib(r_ca_children_plain):
    res = _ca_plain()
    r_arr, r_labels = _r_block_to_array(r_ca_children_plain["row"]["contrib"], 4)
    py = res.row.contrib.loc[r_labels].to_numpy()[:, :4]
    assert np.allclose(py, r_arr, atol=1e-8, rtol=0)


def test_ca_plain_row_inertia(r_ca_children_plain):
    res = _ca_plain()
    r_inertia = np.asarray(r_ca_children_plain["row"]["inertia"], dtype=np.float64)
    py = np.asarray(res.row.inertia, dtype=np.float64)
    assert np.allclose(py, r_inertia, atol=1e-9, rtol=0)


def test_ca_plain_col_coord(r_ca_children_plain):
    res = _ca_plain()
    r_arr, r_labels = _r_block_to_array(r_ca_children_plain["col"]["coord"], 4)
    py = res.col.coord.loc[r_labels].to_numpy()[:, :4]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_ca_plain_col_cos2(r_ca_children_plain):
    res = _ca_plain()
    r_arr, r_labels = _r_block_to_array(r_ca_children_plain["col"]["cos2"], 4)
    py = res.col.cos2.loc[r_labels].to_numpy()[:, :4]
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_ca_plain_col_contrib(r_ca_children_plain):
    res = _ca_plain()
    r_arr, r_labels = _r_block_to_array(r_ca_children_plain["col"]["contrib"], 4)
    py = res.col.contrib.loc[r_labels].to_numpy()[:, :4]
    assert np.allclose(py, r_arr, atol=1e-8, rtol=0)


def test_ca_plain_col_inertia(r_ca_children_plain):
    res = _ca_plain()
    r_inertia = np.asarray(r_ca_children_plain["col"]["inertia"], dtype=np.float64)
    py = np.asarray(res.col.inertia, dtype=np.float64)
    assert np.allclose(py, r_inertia, atol=1e-9, rtol=0)


# ---------------------------------------------------------------------------
# CA on children with supplementary rows + columns
# ---------------------------------------------------------------------------


def _ca_full():
    return CA(
        load_children(), ncp=4,
        row_sup=list(range(14, 18)),
        col_sup=list(range(5, 8)),
    )


def test_ca_full_eigenvalues(r_ca_children):
    res = _ca_full()
    r_eig = np.array([row["eigenvalue"] for row in r_ca_children["eig"]])
    assert np.allclose(res.eig["eigenvalue"].to_numpy(), r_eig, atol=1e-10, rtol=0)


def test_ca_full_row_sup_coord(r_ca_children):
    res = _ca_full()
    r_arr, r_labels = _r_block_to_array(r_ca_children["row.sup"]["coord"], 4)
    py = res.row_sup.coord.loc[r_labels].to_numpy()[:, :4]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-7, rtol=0)


def test_ca_full_row_sup_cos2(r_ca_children):
    res = _ca_full()
    r_arr, r_labels = _r_block_to_array(r_ca_children["row.sup"]["cos2"], 4)
    py = res.row_sup.cos2.loc[r_labels].to_numpy()[:, :4]
    assert np.allclose(py, r_arr, atol=1e-7, rtol=0)


def test_ca_full_col_sup_coord(r_ca_children):
    res = _ca_full()
    r_arr, r_labels = _r_block_to_array(r_ca_children["col.sup"]["coord"], 4)
    py = res.col_sup.coord.loc[r_labels].to_numpy()[:, :4]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-7, rtol=0)


def test_ca_full_col_sup_cos2(r_ca_children):
    res = _ca_full()
    r_arr, r_labels = _r_block_to_array(r_ca_children["col.sup"]["cos2"], 4)
    py = res.col_sup.cos2.loc[r_labels].to_numpy()[:, :4]
    assert np.allclose(py, r_arr, atol=1e-7, rtol=0)
