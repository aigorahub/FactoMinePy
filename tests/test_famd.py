"""FAMD parity tests against R FactoMineR fixtures.

FAMD is a weighted PCA on a mixed [standardized-quanti | scaled-indicator]
matrix. Each output channel is asserted separately against the R FactoMineR
2.14 snapshot of ``FAMD(poison)``:

- ``eig`` (truncated to ncp), ``svd$vs``
- ``ind`` (coord/cos2/contrib/dist)
- ``quanti.var`` (the numeric Age/Time columns: coord/cos2/contrib)
- ``quali.var`` (the 26 categories: coord/cos2/contrib/v.test) — note the
  coord is the *principal* category coordinate, sign-aligned before compare
- ``var`` (combined summary: squared loadings for quanti, eta² for quali —
  sign-invariant, compared directly)

poison's 26 category labels are globally unique, so quali.var rows map by
bare label with no disambiguation needed.
"""

from __future__ import annotations

import numpy as np

from factominer import FAMD
from factominer._sign import align_to_reference
from factominer.datasets import load_poison


def _r_block_to_array(payload, ncp: int) -> tuple[np.ndarray, list[str]]:
    rows, labels = [], []
    for row in payload:
        labels.append(row.get("_row") or row.get("rowname"))
        rows.append([row.get(f"Dim.{i + 1}", row.get(f"Dim {i + 1}")) for i in range(ncp)])
    return np.asarray(rows, dtype=np.float64), labels


def _famd():
    return FAMD(load_poison(), ncp=5)


# ---------------------------------------------------------------------------
# Eigenvalues + SVD
# ---------------------------------------------------------------------------


def test_famd_eigenvalues(r_famd_poison):
    res = _famd()
    r_eig = np.array([row["eigenvalue"] for row in r_famd_poison["eig"]])
    py_eig = res.eig["eigenvalue"].to_numpy()
    assert py_eig.size == r_eig.size, f"py {py_eig.size}, r {r_eig.size}"
    assert np.allclose(py_eig, r_eig, atol=1e-10, rtol=0)


def test_famd_eig_percentages(r_famd_poison):
    res = _famd()
    r_pct = np.array([row["percentage of variance"] for row in r_famd_poison["eig"]])
    r_cum = np.array([row["cumulative percentage of variance"] for row in r_famd_poison["eig"]])
    assert np.allclose(res.eig["percentage of variance"].to_numpy(), r_pct, atol=1e-8)
    assert np.allclose(res.eig["cumulative percentage of variance"].to_numpy(), r_cum, atol=1e-8)


def test_famd_svd_vs(r_famd_poison):
    res = _famd()
    r_vs = np.asarray(r_famd_poison["svd"]["vs"], dtype=np.float64)
    py_vs = res.svd.vs
    n = min(py_vs.size, r_vs.size)
    n_real = int(np.sum(np.abs(r_vs[:n]) > 1e-12))
    assert np.allclose(py_vs[:n_real], r_vs[:n_real], atol=1e-9, rtol=0)


# ---------------------------------------------------------------------------
# Individuals
# ---------------------------------------------------------------------------


def _ind_positional(payload, ncp: int) -> np.ndarray:
    # poison's row index (1..55) serializes as jsonlite "automatic" rownames,
    # which it drops — so the ind rows carry no _row label. R emits them in
    # poison's row order, identical to load_poison() / res.ind.coord order, so
    # we compare positionally (same approach as the MCA tea ind block).
    return np.asarray(
        [[row[f"Dim.{i + 1}"] for i in range(ncp)] for row in payload],
        dtype=np.float64,
    )


def test_famd_ind_coord(r_famd_poison):
    res = _famd()
    r_arr = _ind_positional(r_famd_poison["ind"]["coord"], 5)
    py = res.ind.coord.to_numpy()[:, :5]
    assert r_arr.shape == py.shape, f"{r_arr.shape} vs {py.shape}"
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_famd_ind_cos2(r_famd_poison):
    res = _famd()
    r_arr = _ind_positional(r_famd_poison["ind"]["cos2"], 5)
    py = res.ind.cos2.to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_famd_ind_contrib(r_famd_poison):
    res = _famd()
    r_arr = _ind_positional(r_famd_poison["ind"]["contrib"], 5)
    py = res.ind.contrib.to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-8, rtol=0)


def test_famd_ind_dist(r_famd_poison):
    res = _famd()
    r_dist = r_famd_poison["ind"].get("dist")
    if r_dist is None:
        return
    r = np.asarray(r_dist, dtype=np.float64)
    py = np.asarray(res.ind.dist, dtype=np.float64)
    assert np.allclose(py, r, atol=1e-9, rtol=0)


# ---------------------------------------------------------------------------
# Quantitative variables (Age, Time)
# ---------------------------------------------------------------------------


def test_famd_quanti_var_coord(r_famd_poison):
    res = _famd()
    r_arr, r_labels = _r_block_to_array(r_famd_poison["quanti.var"]["coord"], 5)
    py = res.quanti_var.coord.loc[r_labels].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_famd_quanti_var_cos2(r_famd_poison):
    res = _famd()
    r_arr, r_labels = _r_block_to_array(r_famd_poison["quanti.var"]["cos2"], 5)
    py = res.quanti_var.cos2.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_famd_quanti_var_contrib(r_famd_poison):
    res = _famd()
    r_arr, r_labels = _r_block_to_array(r_famd_poison["quanti.var"]["contrib"], 5)
    py = res.quanti_var.contrib.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-8, rtol=0)


# ---------------------------------------------------------------------------
# Qualitative categories (26 levels across 13 factors)
# ---------------------------------------------------------------------------


def test_famd_quali_var_coord(r_famd_poison):
    res = _famd()
    r_arr, r_labels = _r_block_to_array(r_famd_poison["quali.var"]["coord"], 5)
    py = res.quali_var.coord.loc[r_labels].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_famd_quali_var_cos2(r_famd_poison):
    res = _famd()
    r_arr, r_labels = _r_block_to_array(r_famd_poison["quali.var"]["cos2"], 5)
    py = res.quali_var.cos2.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_famd_quali_var_contrib(r_famd_poison):
    res = _famd()
    r_arr, r_labels = _r_block_to_array(r_famd_poison["quali.var"]["contrib"], 5)
    py = res.quali_var.contrib.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-8, rtol=0)


def test_famd_quali_var_v_test(r_famd_poison):
    res = _famd()
    r_payload = r_famd_poison["quali.var"].get("v.test")
    if r_payload is None:
        return
    r_arr, r_labels = _r_block_to_array(r_payload, 5)
    py = res.quali_var.v_test.loc[r_labels].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


# ---------------------------------------------------------------------------
# Combined variable summary (squared loadings / eta²; sign-invariant)
# ---------------------------------------------------------------------------


def test_famd_var_coord(r_famd_poison):
    res = _famd()
    r_arr, r_labels = _r_block_to_array(r_famd_poison["var"]["coord"], 5)
    py = res.var.coord.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_famd_var_cos2(r_famd_poison):
    res = _famd()
    r_arr, r_labels = _r_block_to_array(r_famd_poison["var"]["cos2"], 5)
    py = res.var.cos2.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_famd_var_contrib(r_famd_poison):
    res = _famd()
    r_arr, r_labels = _r_block_to_array(r_famd_poison["var"]["contrib"], 5)
    py = res.var.contrib.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-8, rtol=0)


def test_famd_summary_runs():
    res = _famd()
    s = res.summary()
    assert "FAMD" in s or "Eigenvalues" in s


# ---------------------------------------------------------------------------
# Supplementary variables: FAMD(poison, sup.var=c("Time","Sex"))
# ---------------------------------------------------------------------------


def _famd_sup():
    return FAMD(load_poison(), ncp=5, sup_var=["Time", "Sex"])


def test_famd_sup_eig(r_famd_poison_sup):
    res = _famd_sup()
    r_eig = np.array([row["eigenvalue"] for row in r_famd_poison_sup["eig"]])
    assert np.allclose(res.eig["eigenvalue"].to_numpy(), r_eig, atol=1e-10, rtol=0)


def test_famd_sup_active_quanti_var(r_famd_poison_sup):
    # active quanti is just Age now (Time is supplementary)
    res = _famd_sup()
    r_arr, r_labels = _r_block_to_array(r_famd_poison_sup["quanti.var"]["coord"], 5)
    py = res.quanti_var.coord.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(align_to_reference(py, r_arr), r_arr, atol=1e-9, rtol=0)


def test_famd_sup_quanti_sup_coord(r_famd_poison_sup):
    res = _famd_sup()
    r_arr, r_labels = _r_block_to_array(r_famd_poison_sup["quanti.sup"]["coord"], 5)
    py = res.quanti_sup.coord.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(align_to_reference(py, r_arr), r_arr, atol=1e-9, rtol=0)


def test_famd_sup_quanti_sup_cos2(r_famd_poison_sup):
    res = _famd_sup()
    r_arr, r_labels = _r_block_to_array(r_famd_poison_sup["quanti.sup"]["cos2"], 5)
    py = res.quanti_sup.cos2.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def _map_quali_sup_rows(py_index, r_labels):
    """Map R's quali.sup labels (bare category) to our 'var=cat' index by the
    bare suffix (same normalization as the PCA quali.sup test)."""
    norm = [lbl.split("=", 1)[-1] for lbl in r_labels]
    py_norm = [s.split("=", 1)[-1] for s in py_index]
    return [py_index[py_norm.index(nm)] for nm in norm]


def test_famd_sup_quali_sup_coord(r_famd_poison_sup):
    res = _famd_sup()
    r_arr, r_labels = _r_block_to_array(r_famd_poison_sup["quali.sup"]["coord"], 5)
    rows = _map_quali_sup_rows(list(res.quali_sup.coord.index), r_labels)
    py = res.quali_sup.coord.loc[rows].to_numpy()[:, :5]
    assert np.allclose(align_to_reference(py, r_arr), r_arr, atol=1e-7, rtol=0)


def test_famd_sup_quali_sup_vtest(r_famd_poison_sup):
    res = _famd_sup()
    payload = r_famd_poison_sup["quali.sup"].get("v.test")
    if payload is None:
        return
    r_arr, r_labels = _r_block_to_array(payload, 5)
    rows = _map_quali_sup_rows(list(res.quali_sup.v_test.index), r_labels)
    py = res.quali_sup.v_test.loc[rows].to_numpy()[:, :5]
    assert np.allclose(align_to_reference(py, r_arr), r_arr, atol=1e-6, rtol=0)


def test_famd_sup_quali_sup_eta2(r_famd_poison_sup):
    res = _famd_sup()
    payload = r_famd_poison_sup["quali.sup"].get("eta2")
    if payload is None:
        return
    r_arr, r_labels = _r_block_to_array(payload, 5)
    py = res.quali_sup.eta2.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_famd_sup_var_coord_sup(r_famd_poison_sup):
    payload = r_famd_poison_sup.get("var.coord.sup")
    if payload is None:
        return
    res = _famd_sup()
    r_arr, r_labels = _r_block_to_array(payload, 5)
    py = res.var.coord_sup.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-8, rtol=0)
