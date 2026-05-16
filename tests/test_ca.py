"""CA parity tests against R FactoMineR fixtures."""

from __future__ import annotations

import numpy as np

from factominer import CA
from factominer._sign import align_to_reference
from factominer.datasets import load_children


def _r_block_to_array(payload, ncp: int) -> tuple[np.ndarray, list[str]]:
    rows, labels = [], []
    for row in payload:
        labels.append(row.get("_row") or row.get("rowname"))
        rows.append([row.get(f"Dim {i + 1}", row.get(f"Dim.{i + 1}")) for i in range(ncp)])
    return np.asarray(rows, dtype=np.float64), labels


def test_ca_plain_eigenvalues(r_ca_children_plain):
    ch = load_children().iloc[:14, :5]
    res = CA(ch, ncp=4)
    r_eig = np.array([row["eigenvalue"] for row in r_ca_children_plain["eig"]])
    assert np.allclose(res.eig["eigenvalue"].to_numpy(), r_eig[: res.eig.shape[0]], atol=1e-8)


def test_ca_plain_row_coord(r_ca_children_plain):
    ch = load_children().iloc[:14, :5]
    res = CA(ch, ncp=4)
    r_arr, r_labels = _r_block_to_array(r_ca_children_plain["row"]["coord"], 4)
    py_arr = res.row.coord.loc[r_labels].to_numpy()[:, :4]
    py_aligned = align_to_reference(py_arr, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-6, rtol=0)


def test_ca_plain_col_coord(r_ca_children_plain):
    ch = load_children().iloc[:14, :5]
    res = CA(ch, ncp=4)
    r_arr, r_labels = _r_block_to_array(r_ca_children_plain["col"]["coord"], 4)
    py_arr = res.col.coord.loc[r_labels].to_numpy()[:, :4]
    py_aligned = align_to_reference(py_arr, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-6, rtol=0)


def test_ca_with_supplementary(r_ca_children):
    ch = load_children()
    # FactoMineR's CA(children, row.sup=15:18, col.sup=6:8) — convert to 0-based positions.
    res = CA(ch, ncp=4, row_sup=list(range(14, 18)), col_sup=list(range(5, 8)))
    r_eig = np.array([row["eigenvalue"] for row in r_ca_children["eig"]])
    assert np.allclose(res.eig["eigenvalue"].to_numpy(), r_eig[: res.eig.shape[0]], atol=1e-8)
    # Supplementary rows: coordinates
    r_rs, r_labels = _r_block_to_array(r_ca_children["row.sup"]["coord"], 4)
    py_rs = res.row_sup.coord.loc[r_labels].to_numpy()[:, :4]
    py_aligned = align_to_reference(py_rs, r_rs)
    assert np.allclose(py_aligned, r_rs, atol=1e-5, rtol=0)
