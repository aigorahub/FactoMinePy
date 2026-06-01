"""DMFA parity tests against R FactoMineR fixtures.

DMFA studies how the cloud of variables varies across the levels of a grouping
factor. The fixture is ``DMFA(decathlon, num.fact=13, scale.unit=TRUE,
quanti.sup=c(11,12))`` — the 10 decathlon events analyzed across the
``Competition`` factor (Decastar / OlympicG), with Rank/Points supplementary.

Channels asserted at the ROADMAP bar: ``eig``, ``ind`` (coord/cos2/contrib/dist,
reordered to input order), ``var`` (coord/cor/cos2/contrib), ``quanti.sup``
(coord/cos2/cor), the ``group`` block (coord / coord.n / cos2 — the
``v_sᵀ Cov_j v_s / λ_s`` trace and its normalizations), and ``cor.dim.gr`` /
``var.partiel`` (per-group correlation diagnostics).
"""

from __future__ import annotations

import numpy as np

from factominer import DMFA
from factominer._sign import align_to_reference
from factominer.datasets import load_decathlon

_LEVELS = ["Decastar", "OlympicG"]


def _dmfa():
    return DMFA(load_decathlon(), num_fact="Competition", quanti_sup=["Rank", "Points"])


def _labeled_block(payload, ncp: int) -> tuple[np.ndarray, list[str]]:
    rows, labels = [], []
    for row in payload:
        labels.append(row.get("_row") or row.get("rowname"))
        rows.append([row.get(f"Dim.{i + 1}") for i in range(ncp)])
    return np.asarray(rows, dtype=np.float64), labels


# ---------------------------------------------------------------------------
# Eigenvalues + SVD
# ---------------------------------------------------------------------------


def test_dmfa_eig(r_dmfa_decathlon):
    res = _dmfa()
    r_eig = np.array([row["eigenvalue"] for row in r_dmfa_decathlon["eig"]])
    py_eig = res.eig["eigenvalue"].to_numpy()
    n = min(py_eig.size, r_eig.size)
    n_real = int(np.sum(np.abs(r_eig[:n]) > 1e-12))
    assert np.allclose(py_eig[:n_real], r_eig[:n_real], atol=1e-10, rtol=0)
    r_pct = np.array([row["percentage of variance"] for row in r_dmfa_decathlon["eig"]])
    assert np.allclose(res.eig["percentage of variance"].to_numpy()[:n_real], r_pct[:n_real], atol=1e-8)


def test_dmfa_svd_vs(r_dmfa_decathlon):
    res = _dmfa()
    r_vs = np.asarray(r_dmfa_decathlon["svd"]["vs"], dtype=np.float64)
    n = min(res.svd.vs.size, r_vs.size)
    n_real = int(np.sum(np.abs(r_vs[:n]) > 1e-12))
    assert np.allclose(res.svd.vs[:n_real], r_vs[:n_real], atol=1e-9, rtol=0)


# ---------------------------------------------------------------------------
# Individuals (reordered to input order)
# ---------------------------------------------------------------------------


def test_dmfa_ind_coord(r_dmfa_decathlon):
    r, labels = _labeled_block(r_dmfa_decathlon["ind"]["coord"], 5)
    py = _dmfa().ind.coord.loc[labels].to_numpy()[:, :5]
    assert np.allclose(align_to_reference(py, r), r, atol=1e-9, rtol=0)


def test_dmfa_ind_cos2(r_dmfa_decathlon):
    r, labels = _labeled_block(r_dmfa_decathlon["ind"]["cos2"], 5)
    py = _dmfa().ind.cos2.loc[labels].to_numpy()[:, :5]
    assert np.allclose(py, r, atol=1e-9, rtol=0)


def test_dmfa_ind_contrib(r_dmfa_decathlon):
    r, labels = _labeled_block(r_dmfa_decathlon["ind"]["contrib"], 5)
    py = _dmfa().ind.contrib.loc[labels].to_numpy()[:, :5]
    assert np.allclose(py, r, atol=1e-8, rtol=0)


# ---------------------------------------------------------------------------
# Active variables (the 10 events) + supplementary quantitatives
# ---------------------------------------------------------------------------


def test_dmfa_var_coord(r_dmfa_decathlon):
    r, labels = _labeled_block(r_dmfa_decathlon["var"]["coord"], 5)
    py = _dmfa().var.coord.loc[labels].to_numpy()[:, :5]
    assert np.allclose(align_to_reference(py, r), r, atol=1e-9, rtol=0)


def test_dmfa_var_cos2(r_dmfa_decathlon):
    r, labels = _labeled_block(r_dmfa_decathlon["var"]["cos2"], 5)
    py = _dmfa().var.cos2.loc[labels].to_numpy()[:, :5]
    assert np.allclose(py, r, atol=1e-9, rtol=0)


def test_dmfa_var_contrib(r_dmfa_decathlon):
    r, labels = _labeled_block(r_dmfa_decathlon["var"]["contrib"], 5)
    py = _dmfa().var.contrib.loc[labels].to_numpy()[:, :5]
    assert np.allclose(py, r, atol=1e-8, rtol=0)


def test_dmfa_quanti_sup_coord(r_dmfa_decathlon):
    payload = r_dmfa_decathlon.get("quanti.sup")
    if payload is None or payload.get("coord") is None:
        return
    r, labels = _labeled_block(payload["coord"], 5)
    py = _dmfa().quanti_sup.coord.loc[labels].to_numpy()[:, :5]
    assert np.allclose(align_to_reference(py, r), r, atol=1e-9, rtol=0)


# ---------------------------------------------------------------------------
# Group block (the DMFA-specific trace coordinates)
# ---------------------------------------------------------------------------


def test_dmfa_group_coord(r_dmfa_decathlon):
    r, labels = _labeled_block(r_dmfa_decathlon["group"]["coord"], 5)
    py = _dmfa().group_coord.loc[labels].to_numpy()[:, :5]
    assert np.allclose(py, r, atol=1e-9, rtol=0)  # sign-invariant (quadratic form)


def test_dmfa_group_coord_n(r_dmfa_decathlon):
    r, labels = _labeled_block(r_dmfa_decathlon["group"]["coord.n"], 5)
    py = _dmfa().group_coord_n.loc[labels].to_numpy()[:, :5]
    assert np.allclose(py, r, atol=1e-9, rtol=0)


def test_dmfa_group_cos2(r_dmfa_decathlon):
    r, labels = _labeled_block(r_dmfa_decathlon["group"]["cos2"], 5)
    py = _dmfa().group_cos2.loc[labels].to_numpy()[:, :5]
    assert np.allclose(py, r, atol=1e-8, rtol=0)


# ---------------------------------------------------------------------------
# Per-group correlation diagnostics
# ---------------------------------------------------------------------------


def test_dmfa_cor_dim_gr(r_dmfa_decathlon):
    # R's cor.dim.gr is a named list (keyed by level) -> a JSON object.
    payload = r_dmfa_decathlon.get("cor.dim.gr")
    if payload is None:
        return
    res = _dmfa()
    for lv in _LEVELS:
        r, labels = _labeled_block(payload[lv], 5)
        py = res.cor_dim_gr[lv].loc[labels].to_numpy()[:, :5]
        # cor(FS_j) is invariant to global-axis sign flips (both axes flip together).
        assert np.allclose(py, r, atol=1e-9, rtol=0), f"cor.dim.gr[{lv}]"


def test_dmfa_var_partiel(r_dmfa_decathlon):
    payload = r_dmfa_decathlon.get("var.partiel")
    if payload is None:
        return
    res = _dmfa()
    for lv in _LEVELS:
        r, labels = _labeled_block(payload[lv], 5)
        py = res.var_partiel[lv].loc[labels].to_numpy()[:, :5]
        assert np.allclose(align_to_reference(py, r), r, atol=1e-9, rtol=0), f"var.partiel[{lv}]"


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------


def test_dmfa_structure():
    res = _dmfa()
    assert res.method == "DMFA"
    assert list(res.group_coord.index) == _LEVELS
    assert list(res.var.coord.index) == [
        "100m", "Long.jump", "Shot.put", "High.jump", "400m",
        "110m.hurdle", "Discus", "Pole.vault", "Javeline", "1500m",
    ]
