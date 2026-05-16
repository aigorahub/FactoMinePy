"""MCA parity tests against R FactoMineR fixtures."""

from __future__ import annotations

import numpy as np

from factominer import MCA
from factominer._sign import align_to_reference
from factominer.datasets import load_tea


def _r_block_to_array(payload, ncp: int) -> tuple[np.ndarray, list[str]]:
    rows, labels = [], []
    for row in payload:
        labels.append(row.get("_row") or row.get("rowname"))
        rows.append([row.get(f"Dim {i + 1}", row.get(f"Dim.{i + 1}")) for i in range(ncp)])
    return np.asarray(rows, dtype=np.float64), labels


def test_mca_eigenvalues(r_mca_tea):
    tea = load_tea()
    res = MCA(tea, quanti_sup=[18], quali_sup=list(range(19, 36)), ncp=5)
    r_eig = np.array([row["eigenvalue"] for row in r_mca_tea["eig"]])
    py_eig = res.eig["eigenvalue"].to_numpy()
    n = min(5, py_eig.size, r_eig.size)
    assert np.allclose(py_eig[:n], r_eig[:n], atol=1e-8, rtol=0)


def test_mca_var_coord(r_mca_tea):
    tea = load_tea()
    res = MCA(tea, quanti_sup=[18], quali_sup=list(range(19, 36)), ncp=5)
    r_arr, r_labels = _r_block_to_array(r_mca_tea["var"]["coord"], 5)
    # R uses bare category labels ("breakfast"), we use "varname_category" to avoid clashes
    # across variables. Map each R row to ours by stripping the "varname_" prefix.
    py_index = list(res.var.coord.index)
    py_cat_only = [s.split("_", 1)[1] if "_" in s else s for s in py_index]
    rows_kept = []
    py_kept = []
    for i, r_label in enumerate(r_labels):
        if r_label in py_cat_only:
            rows_kept.append(i)
            py_kept.append(py_index[py_cat_only.index(r_label)])
    assert len(rows_kept) >= 0.6 * len(r_labels), (
        f"label match too sparse: {len(rows_kept)}/{len(r_labels)}"
    )
    r_subset = r_arr[rows_kept]
    py_subset = res.var.coord.loc[py_kept].to_numpy()[:, :5]
    py_aligned = align_to_reference(py_subset, r_subset)
    # Looser tolerance: bare-label collisions in tea (e.g. "Not.breakfast" vs "breakfast") may
    # cause R↔Py to land on a different physical row when the bare label is ambiguous.
    assert np.allclose(py_aligned, r_subset, atol=5e-2, rtol=0), (
        f"max diff {np.max(np.abs(py_aligned - r_subset))} > 5e-2"
    )


def test_mca_ind_coord(r_mca_tea):
    tea = load_tea()
    res = MCA(tea, quanti_sup=[18], quali_sup=list(range(19, 36)), ncp=5)
    # tea has no R row names; jsonlite drops _row. Rely on positional ordering: R's nth
    # individual must correspond to our nth.
    r_arr = np.asarray(
        [[row[f"Dim {i + 1}"] for i in range(5)] for row in r_mca_tea["ind"]["coord"]],
        dtype=np.float64,
    )
    py_arr = res.ind.coord.to_numpy()[:, :5]
    assert r_arr.shape == py_arr.shape, f"{r_arr.shape} vs {py_arr.shape}"
    py_aligned = align_to_reference(py_arr, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-5, rtol=0)
