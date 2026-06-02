"""MCA parity tests against R FactoMineR fixtures.

Asserts ``eig``, ``svd$vs``, the active ``var`` block (``coord``, ``cos2``,
``contrib``, ``v.test``, ``eta2``), and the ``ind`` block. R's MCA
``var$coord`` is the *standard* category coordinate ψ_c so the R fixture's
values match our ``res.var.coord`` directly; ``var$eta2`` =
``sum_c n_c * ψ_c^2 / N`` (the rescaled-by-q_vars contribution sum).
"""

from __future__ import annotations

import numpy as np
import pytest

from factominer import MCA
from factominer._sign import align_to_reference
from factominer.datasets import load_tea


def _r_block_to_array(payload, ncp: int) -> tuple[np.ndarray, list[str]]:
    rows, labels = [], []
    for row in payload:
        labels.append(row.get("_row") or row.get("rowname"))
        rows.append(
            [row.get(f"Dim {i + 1}", row.get(f"Dim.{i + 1}")) for i in range(ncp)]
        )
    return np.asarray(rows, dtype=np.float64), labels


def _mca():
    return MCA(load_tea(), quanti_sup=[18], quali_sup=list(range(19, 36)), ncp=5)


# Tea's category labels collide across variables ("breakfast" vs "Not.breakfast"
# vs "evening" / "Not.evening" etc.). Our port disambiguates by prefixing the
# variable name; R uses the bare label. Build a lookup so we can map per-test.


def _bare_to_pyindex(py_index: list[str]) -> dict[str, str]:
    by_bare: dict[str, list[str]] = {}
    for label in py_index:
        bare = label.split("_", 1)[1] if "_" in label else label
        by_bare.setdefault(bare, []).append(label)
    return by_bare


def _resolve_r_labels(r_labels: list[str], py_index: list[str], var_for: dict[str, str]):
    """For each R label, pick the matching Python row; skip if ambiguous."""
    bare_to_py = _bare_to_pyindex(py_index)
    chosen_py, kept_idx = [], []
    for i, r_label in enumerate(r_labels):
        candidates = bare_to_py.get(r_label, [])
        var = var_for.get(r_label)
        if var is not None:
            expected = f"{var}_{r_label}"
            if expected in candidates:
                chosen_py.append(expected)
                kept_idx.append(i)
                continue
        if len(candidates) == 1:
            chosen_py.append(candidates[0])
            kept_idx.append(i)
    return chosen_py, kept_idx


def _build_var_for(tea_columns: list[str]) -> dict[str, str]:
    """Map each unique category label to its variable name (when unambiguous)."""
    from factominer.datasets import load_tea
    tea = load_tea()
    var_for: dict[str, list[str]] = {}
    for col in tea_columns:
        if not isinstance(tea[col].dtype, type(tea[col].dtype)):
            continue
        try:
            cats = tea[col].astype("category").cat.categories
        except Exception:
            continue
        for c in cats:
            var_for.setdefault(str(c), []).append(col)
    # Keep only unambiguous mappings (label appears in exactly one variable).
    return {k: v[0] for k, v in var_for.items() if len(v) == 1}


# ---------------------------------------------------------------------------
# Eigenvalues + SVD
# ---------------------------------------------------------------------------


def test_mca_eigenvalues(r_mca_tea):
    res = _mca()
    r_eig = np.array([row["eigenvalue"] for row in r_mca_tea["eig"]])
    py_eig = res.eig["eigenvalue"].to_numpy()
    assert py_eig.size == r_eig.size, f"py {py_eig.size}, r {r_eig.size}"
    assert np.allclose(py_eig, r_eig, atol=1e-10, rtol=0)


def test_mca_eig_percentages(r_mca_tea):
    res = _mca()
    r_pct = np.array([row["percentage of variance"] for row in r_mca_tea["eig"]])
    r_cum = np.array([row["cumulative percentage of variance"] for row in r_mca_tea["eig"]])
    assert np.allclose(res.eig["percentage of variance"].to_numpy(), r_pct, atol=1e-8)
    assert np.allclose(res.eig["cumulative percentage of variance"].to_numpy(), r_cum, atol=1e-8)


def test_mca_svd_vs(r_mca_tea):
    res = _mca()
    r_vs = np.asarray(r_mca_tea["svd"]["vs"], dtype=np.float64)
    py_vs = res.svd.vs
    # Compare real (non-residual) singular values; residuals at ~1e-17 differ
    # across LAPACK builds.
    n_real = int(np.sum(np.abs(r_vs) > 1e-12))
    assert np.allclose(py_vs[:n_real], r_vs[:n_real], atol=1e-9, rtol=0)


# ---------------------------------------------------------------------------
# Per-category active blocks
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def _mca_with_meta():
    res = _mca()
    py_index = list(res.var.coord.index)
    var_for = _build_var_for(load_tea().columns[:18].tolist())
    return res, py_index, var_for


def _kept(r_arr, kept_idx):
    return r_arr[kept_idx]


def test_mca_var_coord(r_mca_tea, _mca_with_meta):
    res, py_index, var_for = _mca_with_meta
    r_arr, r_labels = _r_block_to_array(r_mca_tea["var"]["coord"], 5)
    chosen, kept = _resolve_r_labels(r_labels, py_index, var_for)
    assert len(chosen) >= 0.8 * len(r_labels), (
        f"resolved {len(chosen)}/{len(r_labels)} R labels — disambiguation regressed"
    )
    py = res.var.coord.loc[chosen].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, _kept(r_arr, kept))
    assert np.allclose(py_aligned, _kept(r_arr, kept), atol=1e-9, rtol=0)


def test_mca_var_cos2(r_mca_tea, _mca_with_meta):
    res, py_index, var_for = _mca_with_meta
    r_arr, r_labels = _r_block_to_array(r_mca_tea["var"]["cos2"], 5)
    chosen, kept = _resolve_r_labels(r_labels, py_index, var_for)
    py = res.var.cos2.loc[chosen].to_numpy()[:, :5]
    assert np.allclose(py, _kept(r_arr, kept), atol=1e-9, rtol=0)


def test_mca_var_contrib(r_mca_tea, _mca_with_meta):
    res, py_index, var_for = _mca_with_meta
    r_arr, r_labels = _r_block_to_array(r_mca_tea["var"]["contrib"], 5)
    chosen, kept = _resolve_r_labels(r_labels, py_index, var_for)
    py = res.var.contrib.loc[chosen].to_numpy()[:, :5]
    assert np.allclose(py, _kept(r_arr, kept), atol=1e-8, rtol=0)


def test_mca_var_v_test(r_mca_tea, _mca_with_meta):
    res, py_index, var_for = _mca_with_meta
    r_arr, r_labels = _r_block_to_array(r_mca_tea["var"]["v.test"], 5)
    chosen, kept = _resolve_r_labels(r_labels, py_index, var_for)
    py = res.var.v_test.loc[chosen].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, _kept(r_arr, kept))
    assert np.allclose(py_aligned, _kept(r_arr, kept), atol=1e-9, rtol=0)


def test_mca_var_eta2(r_mca_tea):
    """Per-variable eta² (indexed by variable name, not category — no
    label-collision ambiguity)."""
    res = _mca()
    r_arr, r_labels = _r_block_to_array(r_mca_tea["var"]["eta2"], 5)
    py = res.var.eta2.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


# ---------------------------------------------------------------------------
# Individuals
# ---------------------------------------------------------------------------


def test_mca_ind_coord(r_mca_tea):
    res = _mca()
    r_arr = np.asarray(
        [[row[f"Dim {i + 1}"] for i in range(5)] for row in r_mca_tea["ind"]["coord"]],
        dtype=np.float64,
    )
    py = res.ind.coord.to_numpy()[:, :5]
    assert r_arr.shape == py.shape
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def test_mca_ind_cos2(r_mca_tea):
    res = _mca()
    r_arr = np.asarray(
        [[row[f"Dim {i + 1}"] for i in range(5)] for row in r_mca_tea["ind"]["cos2"]],
        dtype=np.float64,
    )
    py = res.ind.cos2.to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


def test_mca_ind_contrib(r_mca_tea):
    res = _mca()
    r_arr = np.asarray(
        [[row[f"Dim {i + 1}"] for i in range(5)] for row in r_mca_tea["ind"]["contrib"]],
        dtype=np.float64,
    )
    py = res.ind.contrib.to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-8, rtol=0)


# ---------------------------------------------------------------------------
# Supplementary blocks (quanti.sup = age; quali.sup = 17 vars, cols 20-36)
# ---------------------------------------------------------------------------


def test_mca_quanti_sup_coord(r_mca_tea):
    payload = r_mca_tea.get("quanti.sup")
    if payload is None or payload.get("coord") is None:
        return
    res = _mca()
    r_arr, r_labels = _r_block_to_array(payload["coord"], 5)
    py = res.quanti_sup.coord.loc[r_labels].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)


def _sup_var_for():
    return _build_var_for(load_tea().columns[19:36].tolist())


def test_mca_quali_sup_coord(r_mca_tea):
    payload = r_mca_tea.get("quali.sup")
    if payload is None or payload.get("coord") is None:
        return
    res = _mca()
    r_arr, r_labels = _r_block_to_array(payload["coord"], 5)
    chosen, kept = _resolve_r_labels(r_labels, list(res.quali_sup.coord.index), _sup_var_for())
    py = res.quali_sup.coord.loc[chosen].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, _kept(r_arr, kept))
    assert np.allclose(py_aligned, _kept(r_arr, kept), atol=1e-7, rtol=0)


def test_mca_quali_sup_cos2(r_mca_tea):
    payload = r_mca_tea.get("quali.sup")
    if payload is None or payload.get("cos2") is None:
        return
    res = _mca()
    r_arr, r_labels = _r_block_to_array(payload["cos2"], 5)
    chosen, kept = _resolve_r_labels(r_labels, list(res.quali_sup.cos2.index), _sup_var_for())
    py = res.quali_sup.cos2.loc[chosen].to_numpy()[:, :5]
    assert np.allclose(py, _kept(r_arr, kept), atol=1e-7, rtol=0)


def test_mca_quali_sup_vtest(r_mca_tea):
    payload = r_mca_tea.get("quali.sup")
    if payload is None or payload.get("v.test") is None:
        return
    res = _mca()
    r_arr, r_labels = _r_block_to_array(payload["v.test"], 5)
    chosen, kept = _resolve_r_labels(r_labels, list(res.quali_sup.v_test.index), _sup_var_for())
    py = res.quali_sup.v_test.loc[chosen].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, _kept(r_arr, kept))
    assert np.allclose(py_aligned, _kept(r_arr, kept), atol=1e-6, rtol=0)


def test_mca_quali_sup_eta2(r_mca_tea):
    payload = r_mca_tea.get("quali.sup")
    if payload is None or payload.get("eta2") is None:
        return
    res = _mca()
    r_arr, r_labels = _r_block_to_array(payload["eta2"], 5)  # indexed by variable name
    py = res.quali_sup.eta2.loc[r_labels].to_numpy()[:, :5]
    assert np.allclose(py, r_arr, atol=1e-9, rtol=0)


# ---------------------------------------------------------------------------
# Burt method (all-active 8-variable tea slice)
# ---------------------------------------------------------------------------

_BURT_COLS = ["breakfast", "tea.time", "evening", "lunch", "dinner", "Tea", "sugar", "sex"]


def _mca_burt():
    return MCA(load_tea()[_BURT_COLS], ncp=5, method="burt")


def test_mca_burt_eig(r_mca_tea_burt):
    res = _mca_burt()
    r_eig = np.array([row["eigenvalue"] for row in r_mca_tea_burt["eig"]])
    py_eig = res.eig["eigenvalue"].to_numpy()
    assert np.allclose(py_eig, r_eig, atol=1e-10, rtol=0)


def _burt_var_for():
    return _build_var_for(_BURT_COLS)


def test_mca_burt_var_coord(r_mca_tea_burt):
    res = _mca_burt()
    r_arr, r_labels = _r_block_to_array(r_mca_tea_burt["var"]["coord"], 5)
    chosen, kept = _resolve_r_labels(r_labels, list(res.var.coord.index), _burt_var_for())
    py = res.var.coord.loc[chosen].to_numpy()[:, :5]
    py_aligned = align_to_reference(py, _kept(r_arr, kept))
    assert np.allclose(py_aligned, _kept(r_arr, kept), atol=1e-9, rtol=0)


def test_mca_burt_var_cos2(r_mca_tea_burt):
    res = _mca_burt()
    r_arr, r_labels = _r_block_to_array(r_mca_tea_burt["var"]["cos2"], 5)
    chosen, kept = _resolve_r_labels(r_labels, list(res.var.cos2.index), _burt_var_for())
    py = res.var.cos2.loc[chosen].to_numpy()[:, :5]
    assert np.allclose(py, _kept(r_arr, kept), atol=1e-9, rtol=0)


def test_mca_burt_ind_coord(r_mca_tea_burt):
    res = _mca_burt()
    r_arr = np.asarray(
        [[row[f"Dim {i + 1}"] for i in range(5)] for row in r_mca_tea_burt["ind"]["coord"]],
        dtype=np.float64,
    )
    py = res.ind.coord.to_numpy()[:, :5]
    py_aligned = align_to_reference(py, r_arr)
    assert np.allclose(py_aligned, r_arr, atol=1e-9, rtol=0)
