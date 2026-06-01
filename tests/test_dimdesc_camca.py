"""dimdesc parity tests for the CA and MCA branches (R dimdesc.r).

- CA: per axis, the sorted row / column coordinates (active + supplementary).
  Coordinates are sign-dependent, so each axis is sign-aligned before compare.
- MCA: routes through the condes branch — per-variable ``quali`` (R²/p.value,
  sign-invariant) and per-category ``category`` (Estimate sign-dependent).
"""

from __future__ import annotations

import numpy as np

from factominer import CA, MCA, dimdesc
from factominer.datasets import load_children, load_tea


def _ca_desc():
    res = CA(load_children(), row_sup=list(range(14, 18)), col_sup=list(range(5, 8)), ncp=5)
    return dimdesc(res, axes=[0, 1])


def _mca_desc():
    return dimdesc(MCA(load_tea().iloc[:, :6], ncp=5), axes=[0, 1])


def _label_coord(payload) -> dict[str, float]:
    return {str(r.get("_row") or r.get("rowname")): float(r["coord"]) for r in payload}


def _sign_aligned_match(my_map: dict[str, float], r_map: dict[str, float], atol: float) -> bool:
    labels = list(r_map)
    my = np.array([my_map[lbl] for lbl in labels])
    r = np.array([r_map[lbl] for lbl in labels])
    if float(my @ r) < 0:
        my = -my
    return bool(np.allclose(my, r, atol=atol, rtol=0))


def test_dimdesc_ca_row_and_col(r_dimdesc_ca_children):
    d = _ca_desc()
    for i, (_axkey, axpayload) in enumerate(r_dimdesc_ca_children.items()):
        k = [0, 1][i]
        for which in ("row", "col"):
            r_map = _label_coord(axpayload[which])
            my_df = d[k][which]
            my_map = {str(idx): float(v) for idx, v in zip(my_df.index, my_df["coord"], strict=True)}
            assert set(r_map) == set(my_map), f"{which} axis {k}: label set mismatch"
            assert _sign_aligned_match(my_map, r_map, atol=1e-7), f"{which} axis {k}"


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
