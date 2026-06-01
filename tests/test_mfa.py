"""MFA parity tests against R FactoMineR fixtures.

MFA is a single weighted PCA on the horizontal concatenation of per-group
single-table analyses (PCA for type ``"s"`` groups, MCA for type ``"n"``),
each normalized by its first eigenvalue so the groups contribute on an equal
footing. The fixture is the canonical FactoMineR poison MFA:

    MFA(poison, group=c(2,2,5,6), type=c("s","n","n","n"),
        name.group=c("desc","desc2","symptom","eat"))

Every output channel is asserted column-by-column at the ROADMAP parity bar:

- ``eig`` (truncated to ncp.tmp), ``svd$vs``
- ``ind`` (coord/cos2/contrib/dist)
- ``quanti.var`` (Age/Time of the "desc" group: coord/cos2/contrib/cor)
- ``quali.var`` (the 26 categories of the three "n" groups: coord/cos2/contrib/
  v.test) — coord is the supplementary-barycenter principal coordinate,
  sign-aligned before compare
- ``group`` (coord/cos2/contrib/dist2 of the four groups, plus the
  ``(K+1)×(K+1)`` Lg / RV matrices whose last row/column is the global "MFA")

poison's row index is integer (1..55), which jsonlite drops, so the ``ind``
block is compared positionally (as in test_famd). Category, group, quanti.var
labels are stable strings and are mapped by label.
"""

from __future__ import annotations

import numpy as np

from factominer import MFA
from factominer._sign import align_to_reference
from factominer.datasets import load_poison

_GROUP = [2, 2, 5, 6]
_TYPE = ["s", "n", "n", "n"]
_NAME_GROUP = ["desc", "desc2", "symptom", "eat"]


def _mfa():
    return MFA(load_poison(), group=_GROUP, type=_TYPE, name_group=_NAME_GROUP)


def _labeled_block(payload, ncp: int) -> tuple[np.ndarray, list[str]]:
    rows, labels = [], []
    for row in payload:
        labels.append(row.get("_row") or row.get("rowname"))
        rows.append([row.get(f"Dim.{i + 1}") for i in range(ncp)])
    return np.asarray(rows, dtype=np.float64), labels


def _ind_positional(payload, ncp: int) -> np.ndarray:
    # poison's integer rownames serialize as jsonlite "automatic" names (dropped),
    # so ind rows carry no label. R emits them in input order == res.ind.coord
    # order, so compare positionally (same approach as test_famd).
    return np.asarray(
        [[row[f"Dim.{i + 1}"] for i in range(ncp)] for row in payload],
        dtype=np.float64,
    )


def _square_matrix(payload) -> tuple[np.ndarray, list[str]]:
    labels = [str(row.get("_row") or row.get("rowname")) for row in payload]
    arr = np.asarray([[row[lbl] for lbl in labels] for row in payload], dtype=np.float64)
    return arr, labels


# ---------------------------------------------------------------------------
# Eigenvalues + SVD
# ---------------------------------------------------------------------------


def test_mfa_eigenvalues(r_mfa_poison):
    res = _mfa()
    r_eig = np.array([row["eigenvalue"] for row in r_mfa_poison["eig"]])
    py_eig = res.eig["eigenvalue"].to_numpy()
    assert py_eig.size == r_eig.size, f"py {py_eig.size}, r {r_eig.size}"
    assert np.allclose(py_eig, r_eig, atol=1e-10, rtol=0)


def test_mfa_eig_percentages(r_mfa_poison):
    res = _mfa()
    r_pct = np.array([row["percentage of variance"] for row in r_mfa_poison["eig"]])
    r_cum = np.array([row["cumulative percentage of variance"] for row in r_mfa_poison["eig"]])
    assert np.allclose(res.eig["percentage of variance"].to_numpy(), r_pct, atol=1e-8)
    assert np.allclose(res.eig["cumulative percentage of variance"].to_numpy(), r_cum, atol=1e-8)


def test_mfa_svd_vs(r_mfa_poison):
    res = _mfa()
    r_vs = np.asarray(r_mfa_poison["svd"]["vs"], dtype=np.float64)
    py_vs = res.svd.vs
    n = min(py_vs.size, r_vs.size)
    n_real = int(np.sum(np.abs(r_vs[:n]) > 1e-12))
    assert np.allclose(py_vs[:n_real], r_vs[:n_real], atol=1e-9, rtol=0)


# ---------------------------------------------------------------------------
# Individuals
# ---------------------------------------------------------------------------


def test_mfa_ind_coord(r_mfa_poison):
    res = _mfa()
    r_arr = _ind_positional(r_mfa_poison["ind"]["coord"], 5)
    py = res.ind.coord.to_numpy()[:, :5]
    assert r_arr.shape == py.shape, f"{r_arr.shape} vs {py.shape}"
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_mfa_ind_cos2(r_mfa_poison):
    res = _mfa()
    r_arr = _ind_positional(r_mfa_poison["ind"]["cos2"], 5)
    py = res.ind.cos2.to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_mfa_ind_contrib(r_mfa_poison):
    res = _mfa()
    r_arr = _ind_positional(r_mfa_poison["ind"]["contrib"], 5)
    py = res.ind.contrib.to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-8, rtol=0)


# (R MFA's res$ind has no `dist` channel — MFA.R:657 lists only
# coord/contrib/cos2/within.inertia/coord.partiel — so there is nothing to
# assert here, unlike PCA/FAMD where the global ind block carries dist.)


# ---------------------------------------------------------------------------
# Quantitative variables (Age, Time — group "desc", type "s")
# ---------------------------------------------------------------------------


def test_mfa_quanti_var_coord(r_mfa_poison):
    res = _mfa()
    r_arr, r_labels = _labeled_block(r_mfa_poison["quanti.var"]["coord"], 5)
    py = res.quanti_var.coord.loc[r_labels].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_mfa_quanti_var_cos2(r_mfa_poison):
    res = _mfa()
    r_arr, r_labels = _labeled_block(r_mfa_poison["quanti.var"]["cos2"], 5)
    py = res.quanti_var.cos2.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_mfa_quanti_var_contrib(r_mfa_poison):
    res = _mfa()
    r_arr, r_labels = _labeled_block(r_mfa_poison["quanti.var"]["contrib"], 5)
    py = res.quanti_var.contrib.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-8, rtol=0)


def test_mfa_quanti_var_cor(r_mfa_poison):
    res = _mfa()
    r_payload = r_mfa_poison["quanti.var"].get("cor")
    if r_payload is None:
        return
    r_arr, r_labels = _labeled_block(r_payload, 5)
    py = res.quanti_var.cor.loc[r_labels].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


# ---------------------------------------------------------------------------
# Qualitative categories (groups desc2 / symptom / eat)
# ---------------------------------------------------------------------------


def test_mfa_quali_var_coord(r_mfa_poison):
    res = _mfa()
    r_arr, r_labels = _labeled_block(r_mfa_poison["quali.var"]["coord"], 5)
    py = res.quali_var.coord.loc[r_labels].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_mfa_quali_var_cos2(r_mfa_poison):
    res = _mfa()
    r_arr, r_labels = _labeled_block(r_mfa_poison["quali.var"]["cos2"], 5)
    py = res.quali_var.cos2.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_mfa_quali_var_contrib(r_mfa_poison):
    res = _mfa()
    r_arr, r_labels = _labeled_block(r_mfa_poison["quali.var"]["contrib"], 5)
    py = res.quali_var.contrib.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-8, rtol=0)


def test_mfa_quali_var_v_test(r_mfa_poison):
    res = _mfa()
    r_payload = r_mfa_poison["quali.var"].get("v.test")
    if r_payload is None:
        return
    r_arr, r_labels = _labeled_block(r_payload, 5)
    py = res.quali_var.v_test.loc[r_labels].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-6, rtol=0)


# ---------------------------------------------------------------------------
# Groups block (desc / desc2 / symptom / eat, + the MFA Lg/RV matrices)
# ---------------------------------------------------------------------------


def test_mfa_group_coord(r_mfa_poison):
    res = _mfa()
    r_arr, r_labels = _labeled_block(r_mfa_poison["group"]["coord"], 5)
    py = res.group.coord.loc[r_labels].to_numpy()[:, :5]
    # group$coord is a non-negative contribution-to-inertia quantity; align is a
    # no-op but harmless.
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_mfa_group_contrib(r_mfa_poison):
    res = _mfa()
    r_arr, r_labels = _labeled_block(r_mfa_poison["group"]["contrib"], 5)
    py = res.group.contrib.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-8, rtol=0)


def test_mfa_group_cos2(r_mfa_poison):
    res = _mfa()
    r_arr, r_labels = _labeled_block(r_mfa_poison["group"]["cos2"], 5)
    py = res.group.cos2.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_mfa_group_dist2(r_mfa_poison):
    res = _mfa()
    r_dist2 = r_mfa_poison["group"].get("dist2")
    if r_dist2 is None:
        return
    r = np.asarray(r_dist2, dtype=np.float64)
    py = np.asarray(res.group.dist2, dtype=np.float64)
    assert np.allclose(py, r, atol=1e-9, rtol=0)


def test_mfa_group_Lg(r_mfa_poison):
    res = _mfa()
    r_payload = r_mfa_poison["group"].get("Lg")
    if r_payload is None:
        return
    r_arr, r_labels = _square_matrix(r_payload)
    py = res.group.Lg.loc[r_labels, r_labels].to_numpy()
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_mfa_group_RV(r_mfa_poison):
    res = _mfa()
    r_payload = r_mfa_poison["group"].get("RV")
    if r_payload is None:
        return
    r_arr, r_labels = _square_matrix(r_payload)
    py = res.group.RV.loc[r_labels, r_labels].to_numpy()
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


# ---------------------------------------------------------------------------
# A2: partial factor maps / partial axes / group correlation / inertia ratio
# ---------------------------------------------------------------------------


def test_mfa_ind_coord_partiel(r_mfa_poison):
    """Per-group partial individual coordinates ((n·K) × ncp, row '<ind>.<group>')."""
    payload = r_mfa_poison.get("ind.coord.partiel")
    if payload is None:
        return
    r_arr, r_labels = _labeled_block(payload, 5)
    res = _mfa()
    py = res.ind.coord_partiel.loc[r_labels].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_mfa_group_correlation(r_mfa_poison):
    payload = r_mfa_poison["group"].get("correlation")
    if payload is None:
        return
    r_arr, r_labels = _labeled_block(payload, 5)
    res = _mfa()
    py = res.group.correlation.loc[r_labels].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_mfa_partial_axes_coord(r_mfa_poison):
    pax = r_mfa_poison.get("partial.axes")
    if pax is None or pax.get("coord") is None:
        return
    r_arr, r_labels = _labeled_block(pax["coord"], 5)
    res = _mfa()
    py = res.partial_axes.coord.loc[r_labels].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_mfa_partial_axes_cor(r_mfa_poison):
    pax = r_mfa_poison.get("partial.axes")
    if pax is None or pax.get("cor") is None:
        return
    r_arr, r_labels = _labeled_block(pax["cor"], 5)
    res = _mfa()
    py = res.partial_axes.cor.loc[r_labels].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_mfa_partial_axes_contrib(r_mfa_poison):
    pax = r_mfa_poison.get("partial.axes")
    if pax is None or pax.get("contrib") is None:
        return
    r_arr, r_labels = _labeled_block(pax["contrib"], 5)
    res = _mfa()
    py = res.partial_axes.contrib.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-8, rtol=0)


def test_mfa_inertia_ratio(r_mfa_poison):
    payload = r_mfa_poison.get("inertia.ratio")
    if payload is None:
        return
    r = np.asarray(payload, dtype=np.float64)
    res = _mfa()
    py = res.inertia_ratio.to_numpy()
    assert np.allclose(py, r, atol=1e-9, rtol=0)


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------


def test_mfa_summary_runs():
    res = _mfa()
    s = res.summary()
    assert "MFA" in s or "Eigenvalues" in s
