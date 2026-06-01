"""HMFA parity tests against R FactoMineR fixtures.

HMFA = a single weighted PCA on the level-1-standardized data matrix (R's
``XTDC``), with column weights that accumulate one ``1/λ₁`` per hierarchy level.
Two fixtures exercise it:

- ``hmfa/poison.json`` — the categorical-heavy 2-level hierarchy
  ``HMFA(poison, H=list(c(2,2,5,6), c(2,2)), type=c("s","n","n","n"))`` (level-2
  super-groups: description={desc,desc2}, signs={symptom,eat}).
- ``hmfa/decathlon.json`` — a pure-quanti sanity check
  ``HMFA(decathlon[,1:10], H=list(c(4,3,3), c(1,2)), type=rep("s",3))``.

Channels asserted at the ROADMAP bar: ``eig``, ``ind`` (coord/cos2/contrib/dist),
``quanti.var`` (coord/cor/cos2/contrib), ``quali.var`` (coord/contrib, poison
only), and the ``group`` block — ``coord`` (a list, one matrix per hierarchy
level) and ``canonical`` (canonical correlations per node).
"""

from __future__ import annotations

import numpy as np

from factominer import HMFA
from factominer._sign import align_to_reference
from factominer.datasets import load_decathlon, load_poison

_POISON_H = [[2, 2, 5, 6], [2, 2]]
_POISON_TYPE = ["s", "n", "n", "n"]
_DECA_H = [[4, 3, 3], [1, 2]]


def _hmfa_poison():
    return HMFA(load_poison(), H=_POISON_H, type=_POISON_TYPE)


def _hmfa_decathlon():
    return HMFA(load_decathlon().iloc[:, :10], H=_DECA_H, type=["s", "s", "s"])


def _labeled_block(payload, ncp: int) -> tuple[np.ndarray, list[str]]:
    rows, labels = [], []
    for row in payload:
        labels.append(row.get("_row") or row.get("rowname"))
        rows.append([row.get(f"Dim.{i + 1}") for i in range(ncp)])
    return np.asarray(rows, dtype=np.float64), labels


def _positional(payload, ncp: int) -> np.ndarray:
    return np.asarray(
        [[row[f"Dim.{i + 1}"] for i in range(ncp)] for row in payload], dtype=np.float64
    )


# ---------------------------------------------------------------------------
# Eigenvalues
# ---------------------------------------------------------------------------


def _assert_eig(res, r_fixture):
    r_eig = np.array([row["eigenvalue"] for row in r_fixture["eig"]])
    py_eig = res.eig["eigenvalue"].to_numpy()
    n = min(py_eig.size, r_eig.size)
    n_real = int(np.sum(np.abs(r_eig[:n]) > 1e-12))
    assert np.allclose(py_eig[:n_real], r_eig[:n_real], atol=1e-10, rtol=0)
    r_pct = np.array([row["percentage of variance"] for row in r_fixture["eig"]])
    assert np.allclose(res.eig["percentage of variance"].to_numpy()[:n_real], r_pct[:n_real], atol=1e-8)


def test_hmfa_poison_eig(r_hmfa_poison):
    _assert_eig(_hmfa_poison(), r_hmfa_poison)


def test_hmfa_decathlon_eig(r_hmfa_decathlon):
    _assert_eig(_hmfa_decathlon(), r_hmfa_decathlon)


# ---------------------------------------------------------------------------
# Individuals
# ---------------------------------------------------------------------------


def test_hmfa_poison_ind_coord(r_hmfa_poison):
    # poison integer rownames are dropped by jsonlite -> positional compare.
    r = _positional(r_hmfa_poison["ind"]["coord"], 5)
    py = _hmfa_poison().ind.coord.to_numpy()[:, :5]
    assert np.allclose(align_to_reference(py, r), r, atol=1e-9, rtol=0)


def test_hmfa_poison_ind_cos2(r_hmfa_poison):
    r = _positional(r_hmfa_poison["ind"]["cos2"], 5)
    py = _hmfa_poison().ind.cos2.to_numpy()[:, :5]
    assert np.allclose(py, r, atol=1e-9, rtol=0)


def test_hmfa_poison_ind_contrib(r_hmfa_poison):
    r = _positional(r_hmfa_poison["ind"]["contrib"], 5)
    py = _hmfa_poison().ind.contrib.to_numpy()[:, :5]
    assert np.allclose(py, r, atol=1e-8, rtol=0)


def test_hmfa_decathlon_ind_coord(r_hmfa_decathlon):
    # decathlon has string rownames -> labelled compare.
    r, labels = _labeled_block(r_hmfa_decathlon["ind"]["coord"], 5)
    py = _hmfa_decathlon().ind.coord.loc[labels].to_numpy()[:, :5]
    assert np.allclose(align_to_reference(py, r), r, atol=1e-9, rtol=0)


def test_hmfa_decathlon_ind_dist(r_hmfa_decathlon):
    r_dist = r_hmfa_decathlon["ind"].get("dist")
    if r_dist is None:
        return
    res = _hmfa_decathlon()
    # R emits ind rows in input order == res.ind.coord order.
    py = np.asarray(res.ind.dist, dtype=np.float64)
    assert np.allclose(py, np.asarray(r_dist, dtype=np.float64), atol=1e-9, rtol=0)


# ---------------------------------------------------------------------------
# Quantitative variables
# ---------------------------------------------------------------------------


def _assert_quanti(res, r_fixture):
    r_coord, labels = _labeled_block(r_fixture["quanti.var"]["coord"], 5)
    py = res.quanti_var.coord.loc[labels].to_numpy()[:, :5]
    assert np.allclose(align_to_reference(py, r_coord), r_coord, atol=1e-9, rtol=0)
    r_cos2, _ = _labeled_block(r_fixture["quanti.var"]["cos2"], 5)
    assert np.allclose(res.quanti_var.cos2.loc[labels].to_numpy()[:, :5], r_cos2, atol=1e-9, rtol=0)
    r_contrib, _ = _labeled_block(r_fixture["quanti.var"]["contrib"], 5)
    assert np.allclose(
        res.quanti_var.contrib.loc[labels].to_numpy()[:, :5], r_contrib, atol=1e-8, rtol=0
    )
    if r_fixture["quanti.var"].get("cor") is not None:
        r_cor, _ = _labeled_block(r_fixture["quanti.var"]["cor"], 5)
        py_cor = res.quanti_var.cor.loc[labels].to_numpy()[:, :5]
        assert np.allclose(align_to_reference(py_cor, r_cor), r_cor, atol=1e-9, rtol=0)


def test_hmfa_poison_quanti_var(r_hmfa_poison):
    _assert_quanti(_hmfa_poison(), r_hmfa_poison)


def test_hmfa_decathlon_quanti_var(r_hmfa_decathlon):
    _assert_quanti(_hmfa_decathlon(), r_hmfa_decathlon)


# ---------------------------------------------------------------------------
# Qualitative variables (poison only)
# ---------------------------------------------------------------------------


def test_hmfa_poison_quali_var_coord(r_hmfa_poison):
    r, labels = _labeled_block(r_hmfa_poison["quali.var"]["coord"], 5)
    py = _hmfa_poison().quali_var.coord.loc[labels].to_numpy()[:, :5]
    assert np.allclose(align_to_reference(py, r), r, atol=1e-9, rtol=0)


def test_hmfa_poison_quali_var_contrib(r_hmfa_poison):
    r, labels = _labeled_block(r_hmfa_poison["quali.var"]["contrib"], 5)
    py = _hmfa_poison().quali_var.contrib.loc[labels].to_numpy()[:, :5]
    assert np.allclose(py, r, atol=1e-8, rtol=0)


# ---------------------------------------------------------------------------
# Group block (per-level coord list + canonical correlations)
# ---------------------------------------------------------------------------


def _assert_group(res, r_fixture):
    coord_levels = r_fixture["group"]["coord"]
    assert len(coord_levels) == len(res.group_coord)
    for h, level_payload in enumerate(coord_levels):
        r_arr, labels = _labeled_block(level_payload, 5)
        py = res.group_coord[h].loc[labels].to_numpy()[:, :5]
        # group$coord is a non-negative weighted sum of squared loadings.
        assert np.allclose(py, r_arr, atol=1e-9, rtol=0), f"group.coord level {h + 1}"
    r_canon, canon_labels = _labeled_block(r_fixture["group"]["canonical"], 5)
    py_canon = res.group_canonical.loc[canon_labels].to_numpy()[:, :5]
    assert np.allclose(py_canon, r_canon, atol=1e-9, rtol=0), "group.canonical"


def test_hmfa_poison_group(r_hmfa_poison):
    _assert_group(_hmfa_poison(), r_hmfa_poison)


def test_hmfa_decathlon_group(r_hmfa_decathlon):
    _assert_group(_hmfa_decathlon(), r_hmfa_decathlon)


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------


def test_hmfa_structure():
    res = _hmfa_poison()
    assert res.method == "HMFA"
    assert len(res.group_coord) == 2
    assert res.group_coord[0].shape[0] == 4 and res.group_coord[1].shape[0] == 2
    assert res.group_canonical.shape[0] == 6
    assert len(res.partial) == 2
