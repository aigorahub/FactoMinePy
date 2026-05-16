"""PCA parity tests against R FactoMineR fixtures.

Each test asserts a single output channel against the JSON snapshot of R
FactoMineR's output for the same model spec, so a regression in any column of
``eig``, ``var``, ``ind``, ``quanti.sup``, or ``quali.sup`` (including
``quali.sup$eta2``, which is per-variable rather than per-category) trips a
specific test rather than a blanket smoke check.
"""

from __future__ import annotations

import numpy as np

from factominer import PCA
from factominer._sign import align_to_reference
from factominer.datasets import load_decathlon


def _r_block_to_array(payload, ncp: int) -> tuple[np.ndarray, list[str]]:
    rows, labels = [], []
    for row in payload:
        labels.append(row.get("_row") or row.get("rowname"))
        rows.append([row[f"Dim.{i + 1}"] for i in range(ncp)])
    return np.asarray(rows, dtype=np.float64), labels


# ---------------------------------------------------------------------------
# Plain PCA on decathlon (no supplementary blocks)
# ---------------------------------------------------------------------------


def _pca_plain():
    return PCA(load_decathlon().iloc[:, :10], scale_unit=True, ncp=5)


def test_pca_plain_eigenvalues(r_pca_decathlon_plain):
    res = _pca_plain()
    r_eig = np.array([row["eigenvalue"] for row in r_pca_decathlon_plain["eig"]])
    assert np.allclose(res.eig["eigenvalue"].to_numpy(), r_eig, atol=1e-10, rtol=0)


def test_pca_plain_eig_percentages(r_pca_decathlon_plain):
    res = _pca_plain()
    r_pct = np.array([row["percentage of variance"] for row in r_pca_decathlon_plain["eig"]])
    r_cum = np.array(
        [row["cumulative percentage of variance"] for row in r_pca_decathlon_plain["eig"]]
    )
    py_pct = res.eig["percentage of variance"].to_numpy()
    py_cum = res.eig["cumulative percentage of variance"].to_numpy()
    assert np.allclose(py_pct, r_pct, atol=1e-8, rtol=0)
    assert np.allclose(py_cum, r_cum, atol=1e-8, rtol=0)


def test_pca_plain_svd_vs(r_pca_decathlon_plain):
    res = _pca_plain()
    r_vs = np.asarray(r_pca_decathlon_plain["svd"]["vs"], dtype=np.float64)
    py_vs = res.svd.vs
    # Real singular values match tightly; residual ones (≈ 1e-17) differ across
    # LAPACK builds. Compare only the real part.
    n_real = int(np.sum(np.abs(r_vs) > 1e-12))
    assert np.allclose(py_vs[:n_real], r_vs[:n_real], atol=1e-9, rtol=0)


def test_pca_plain_var_coord(r_pca_decathlon_plain):
    res = _pca_plain()
    r_arr, r_labels = _r_block_to_array(r_pca_decathlon_plain["var"]["coord"], 5)
    py = res.var.coord.loc[r_labels].to_numpy()
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_pca_plain_var_cor(r_pca_decathlon_plain):
    res = _pca_plain()
    # In scaled PCA, var$cor == var$coord (correlations equal the loadings).
    r_arr, r_labels = _r_block_to_array(r_pca_decathlon_plain["var"]["cor"], 5)
    py = res.var.cor.loc[r_labels].to_numpy()
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_pca_plain_var_cos2(r_pca_decathlon_plain):
    res = _pca_plain()
    r_arr, r_labels = _r_block_to_array(r_pca_decathlon_plain["var"]["cos2"], 5)
    py = res.var.cos2.loc[r_labels].to_numpy()
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_pca_plain_var_contrib(r_pca_decathlon_plain):
    res = _pca_plain()
    r_arr, r_labels = _r_block_to_array(r_pca_decathlon_plain["var"]["contrib"], 5)
    py = res.var.contrib.loc[r_labels].to_numpy()
    assert np.allclose(py, r_arr, atol=1e-8, rtol=0)


def test_pca_plain_ind_coord(r_pca_decathlon_plain):
    res = _pca_plain()
    r_arr, r_labels = _r_block_to_array(r_pca_decathlon_plain["ind"]["coord"], 5)
    py = res.ind.coord.loc[r_labels].to_numpy()
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_pca_plain_ind_cos2(r_pca_decathlon_plain):
    res = _pca_plain()
    r_arr, r_labels = _r_block_to_array(r_pca_decathlon_plain["ind"]["cos2"], 5)
    py = res.ind.cos2.loc[r_labels].to_numpy()
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_pca_plain_ind_contrib(r_pca_decathlon_plain):
    res = _pca_plain()
    r_arr, r_labels = _r_block_to_array(r_pca_decathlon_plain["ind"]["contrib"], 5)
    py = res.ind.contrib.loc[r_labels].to_numpy()
    assert np.allclose(py, r_arr, atol=1e-8, rtol=0)


def test_pca_plain_ind_dist(r_pca_decathlon_plain):
    res = _pca_plain()
    r_dist_payload = r_pca_decathlon_plain["ind"].get("dist")
    if r_dist_payload is None:
        return
    r_dist = np.asarray(r_dist_payload, dtype=np.float64)
    py_dist = np.asarray(res.ind.dist, dtype=np.float64)
    # R's ind$dist is signed-squared-distance; we store the same scalar.
    # Order matches the R fixture's index order, which mirrors res.ind.coord.
    assert np.allclose(py_dist, r_dist, atol=1e-9, rtol=0)


# ---------------------------------------------------------------------------
# Full PCA on decathlon with sups
# ---------------------------------------------------------------------------


def _pca_full():
    return PCA(
        load_decathlon(),
        scale_unit=True,
        ncp=5,
        quanti_sup=["Rank", "Points"],
        quali_sup=["Competition"],
    )


def test_pca_full_eigenvalues(r_pca_decathlon):
    res = _pca_full()
    r_eig = np.array([row["eigenvalue"] for row in r_pca_decathlon["eig"]])
    assert np.allclose(res.eig["eigenvalue"].to_numpy(), r_eig, atol=1e-10, rtol=0)


def test_pca_full_quanti_sup_coord(r_pca_decathlon):
    res = _pca_full()
    r_arr, r_labels = _r_block_to_array(r_pca_decathlon["quanti.sup"]["coord"], 5)
    py = res.quanti_sup.coord.loc[r_labels].to_numpy()
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_pca_full_quanti_sup_cor(r_pca_decathlon):
    res = _pca_full()
    r_arr, r_labels = _r_block_to_array(r_pca_decathlon["quanti.sup"]["cor"], 5)
    py = res.quanti_sup.cor.loc[r_labels].to_numpy()
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_pca_full_quanti_sup_cos2(r_pca_decathlon):
    res = _pca_full()
    r_arr, r_labels = _r_block_to_array(r_pca_decathlon["quanti.sup"]["cos2"], 5)
    py = res.quanti_sup.cos2.loc[r_labels].to_numpy()
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_pca_full_quali_sup_coord(r_pca_decathlon):
    res = _pca_full()
    r_arr, r_labels = _r_block_to_array(r_pca_decathlon["quali.sup"]["coord"], 5)
    # FactoMineR labels per-category as e.g. "Decastar" / "OlympicG"; we label as
    # "Competition=Decastar" / "Competition=OlympicG". Strip the prefix.
    norm_labels = [lbl.split("=", 1)[-1] for lbl in r_labels]
    py_index = list(res.quali_sup.coord.index)
    py_norm = [s.split("=", 1)[-1] for s in py_index]
    py_rows = [py_index[py_norm.index(n)] for n in norm_labels]
    py = res.quali_sup.coord.loc[py_rows].to_numpy()
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-7, rtol=0)


def test_pca_full_quali_sup_cos2(r_pca_decathlon):
    res = _pca_full()
    r_arr, r_labels = _r_block_to_array(r_pca_decathlon["quali.sup"]["cos2"], 5)
    norm = [lbl.split("=", 1)[-1] for lbl in r_labels]
    py_index = list(res.quali_sup.cos2.index)
    py_rows = [py_index[[s.split("=", 1)[-1] for s in py_index].index(n)] for n in norm]
    py = res.quali_sup.cos2.loc[py_rows].to_numpy()
    assert np.allclose(py, r_arr, atol=1e-7, rtol=0)


def test_pca_full_quali_sup_vtest(r_pca_decathlon):
    res = _pca_full()
    r_arr, r_labels = _r_block_to_array(r_pca_decathlon["quali.sup"]["v.test"], 5)
    norm = [lbl.split("=", 1)[-1] for lbl in r_labels]
    py_index = list(res.quali_sup.v_test.index)
    py_rows = [py_index[[s.split("=", 1)[-1] for s in py_index].index(n)] for n in norm]
    py = res.quali_sup.v_test.loc[py_rows].to_numpy()
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-7, rtol=0)


def test_pca_full_quali_sup_eta2(r_pca_decathlon):
    res = _pca_full()
    r_arr, r_labels = _r_block_to_array(r_pca_decathlon["quali.sup"]["eta2"], 5)
    assert res.quali_sup.eta2 is not None, (
        "PCA quali.sup must expose eta2 (per-variable, not per-category)"
    )
    py = res.quali_sup.eta2.loc[r_labels].to_numpy()
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_pca_summary_has_expected_sections():
    res = _pca_full()
    s = res.summary()
    assert "Eigenvalues" in s
    assert "Individuals" in s
    assert "Variables" in s
    assert "Supplementary continuous variables" in s
