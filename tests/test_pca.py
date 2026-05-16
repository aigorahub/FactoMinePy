"""PCA parity tests against R FactoMineR fixtures."""

from __future__ import annotations

import numpy as np

from factominer import PCA
from factominer._sign import align_to_reference
from factominer.datasets import load_decathlon


def _r_block_to_array(payload, ncp: int) -> tuple[np.ndarray, list[str]]:
    """Convert a list-of-objects payload into (array, row_labels)."""
    rows = []
    labels = []
    for row in payload:
        labels.append(row.get("_row") or row.get("rowname"))
        rows.append([row[f"Dim.{i + 1}"] for i in range(ncp)])
    return np.asarray(rows, dtype=np.float64), labels


def test_pca_eigenvalues_match_r(r_pca_decathlon_plain):
    df = load_decathlon().iloc[:, :10]
    res = PCA(df, scale_unit=True, ncp=5)
    r_eig = np.array([row["eigenvalue"] for row in r_pca_decathlon_plain["eig"]])
    py_eig = res.eig["eigenvalue"].to_numpy()
    assert np.allclose(py_eig, r_eig[: py_eig.size], atol=1e-8, rtol=0)


def test_pca_percentages_match_r(r_pca_decathlon_plain):
    df = load_decathlon().iloc[:, :10]
    res = PCA(df, scale_unit=True, ncp=5)
    r_pct = np.array([row["percentage of variance"] for row in r_pca_decathlon_plain["eig"]])
    py_pct = res.eig["percentage of variance"].to_numpy()
    assert np.allclose(py_pct, r_pct[: py_pct.size], atol=1e-6, rtol=0)


def test_pca_var_coord_match_r(r_pca_decathlon_plain):
    df = load_decathlon().iloc[:, :10]
    res = PCA(df, scale_unit=True, ncp=5)
    r_var, r_labels = _r_block_to_array(r_pca_decathlon_plain["var"]["coord"], 5)
    py_var = res.var.coord.loc[r_labels].to_numpy()
    py_aligned = align_to_reference(py_var, r_var)
    assert np.allclose(py_aligned, r_var, atol=1e-6, rtol=0)


def test_pca_var_cos2_match_r(r_pca_decathlon_plain):
    df = load_decathlon().iloc[:, :10]
    res = PCA(df, scale_unit=True, ncp=5)
    r_cos2, r_labels = _r_block_to_array(r_pca_decathlon_plain["var"]["cos2"], 5)
    py_cos2 = res.var.cos2.loc[r_labels].to_numpy()
    assert np.allclose(py_cos2, r_cos2, atol=1e-6, rtol=0)


def test_pca_var_contrib_match_r(r_pca_decathlon_plain):
    df = load_decathlon().iloc[:, :10]
    res = PCA(df, scale_unit=True, ncp=5)
    r_contrib, r_labels = _r_block_to_array(r_pca_decathlon_plain["var"]["contrib"], 5)
    py_contrib = res.var.contrib.loc[r_labels].to_numpy()
    assert np.allclose(py_contrib, r_contrib, atol=1e-6, rtol=0)


def test_pca_ind_coord_match_r(r_pca_decathlon_plain):
    df = load_decathlon().iloc[:, :10]
    res = PCA(df, scale_unit=True, ncp=5)
    r_ind, r_labels = _r_block_to_array(r_pca_decathlon_plain["ind"]["coord"], 5)
    py_ind = res.ind.coord.loc[r_labels].to_numpy()
    py_aligned = align_to_reference(py_ind, r_ind)
    assert np.allclose(py_aligned, r_ind, atol=1e-6, rtol=0)


def test_pca_ind_cos2_match_r(r_pca_decathlon_plain):
    df = load_decathlon().iloc[:, :10]
    res = PCA(df, scale_unit=True, ncp=5)
    r_cos2, r_labels = _r_block_to_array(r_pca_decathlon_plain["ind"]["cos2"], 5)
    py_cos2 = res.ind.cos2.loc[r_labels].to_numpy()
    assert np.allclose(py_cos2, r_cos2, atol=1e-6, rtol=0)


def test_pca_ind_contrib_match_r(r_pca_decathlon_plain):
    df = load_decathlon().iloc[:, :10]
    res = PCA(df, scale_unit=True, ncp=5)
    r_contrib, r_labels = _r_block_to_array(r_pca_decathlon_plain["ind"]["contrib"], 5)
    py_contrib = res.ind.contrib.loc[r_labels].to_numpy()
    assert np.allclose(py_contrib, r_contrib, atol=1e-6, rtol=0)


def test_pca_with_supplementary_blocks(r_pca_decathlon):
    """Smoke + structural tests for the full decathlon PCA with sup blocks."""
    df = load_decathlon()
    res = PCA(df, scale_unit=True, ncp=5,
              quanti_sup=["Rank", "Points"], quali_sup=["Competition"])
    # Eigenvalues should match (sup blocks don't affect the active analysis)
    r_eig = np.array([row["eigenvalue"] for row in r_pca_decathlon["eig"]])
    assert np.allclose(res.eig["eigenvalue"].to_numpy(), r_eig[: res.eig.shape[0]], atol=1e-8)
    # Supplementary quantitative variables: coordinates align
    r_qs, r_labels = _r_block_to_array(r_pca_decathlon["quanti.sup"]["coord"], 5)
    py_qs = res.quanti_sup.coord.loc[r_labels].to_numpy()
    py_aligned = align_to_reference(py_qs, r_qs)
    # Looser tolerance for sup blocks; correlation-vs-coord conventions can drift slightly
    assert np.allclose(py_aligned, r_qs, atol=1e-5, rtol=0)


def test_pca_summary_has_expected_sections():
    df = load_decathlon()
    res = PCA(df, scale_unit=True, ncp=3,
              quanti_sup=["Rank", "Points"], quali_sup=["Competition"])
    s = res.summary()
    assert "Eigenvalues" in s
    assert "Individuals" in s
    assert "Variables" in s
    assert "Supplementary continuous variables" in s
