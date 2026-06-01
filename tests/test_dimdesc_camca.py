"""dimdesc parity tests for the CA and MCA branches (R dimdesc.r).

- CA: per axis, the sorted row / column coordinates (active + supplementary).
  Coordinates are sign-dependent, so each axis is sign-aligned before compare.
- MCA: routes through the condes branch — per-variable ``quali`` (R²/p.value,
  sign-invariant) and per-category ``category`` (Estimate sign-dependent).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from factominer import CA, MCA, dimdesc
from factominer.datasets import load_children, load_tea


def _mca_desc():
    return dimdesc(MCA(load_tea().iloc[:, :6], ncp=5), axes=[0, 1])


def test_dimdesc_ca_self_consistent():
    # R FactoMineR 2.14's dimdesc(CA) errors on R 4.x (order on a 1-col data
    # frame), so there is no R fixture. The CA branch is a pure re-sort of the
    # (R-parity-verified) CA coordinates, so verify it against those directly:
    # each axis's row/col table = the active+supplementary coords sorted ascending.
    res = CA(load_children(), row_sup=list(range(14, 18)), col_sup=list(range(5, 8)), ncp=5)
    d = dimdesc(res, axes=[0, 1])
    full_row = pd.concat([res.row.coord, res.row_sup.coord])
    full_col = pd.concat([res.col.coord, res.col_sup.coord])
    for k in (0, 1):
        for tbl, full in (("row", full_row), ("col", full_col)):
            expected = full.iloc[:, k].sort_values()
            got = d[k][tbl]["coord"]
            assert list(got.index) == list(expected.index), f"{tbl} axis {k} order"
            assert np.allclose(got.to_numpy(), expected.to_numpy(), atol=1e-12), f"{tbl} axis {k}"
            assert list(d[k][tbl].columns) == ["coord"]


def test_dimdesc_mca_quali(r_dimdesc_mca_tea):
    d = _mca_desc()
    for i, (_axkey, axpayload) in enumerate(r_dimdesc_mca_tea.items()):
        payload = axpayload.get("quali")
        if payload is None:
            continue
        k = [0, 1][i]
        for row in payload:
            var = str(row.get("_row") or row.get("rowname"))
            assert var in d[k]["quali"].index, f"quali var {var} missing on axis {k}"
            assert np.isclose(d[k]["quali"].loc[var, "R2"], row["R2"], atol=1e-7), f"{var} R2"
            assert np.isclose(
                d[k]["quali"].loc[var, "p.value"], row["p.value"], atol=1e-6
            ), f"{var} p.value"


def test_dimdesc_mca_category_count(r_dimdesc_mca_tea):
    # The category Estimate is sign-dependent and the labels can collide across
    # variables; assert the per-axis category count and p.value set match R.
    d = _mca_desc()
    for i, (_axkey, axpayload) in enumerate(r_dimdesc_mca_tea.items()):
        payload = axpayload.get("category")
        if payload is None:
            continue
        k = [0, 1][i]
        r_pvals = sorted(float(r["p.value"]) for r in payload)
        py_pvals = sorted(float(v) for v in d[k]["category"]["p.value"])
        assert len(r_pvals) == len(py_pvals), f"category count axis {k}"
        assert np.allclose(py_pvals, r_pvals, atol=1e-6, rtol=0), f"category p.values axis {k}"
