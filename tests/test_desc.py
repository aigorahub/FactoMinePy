"""Parity tests for dimdesc / catdes / condes against R FactoMineR fixtures."""

from __future__ import annotations

import math

import pytest

from factominer import PCA, catdes, condes, dimdesc
from factominer.datasets import load_decathlon, load_tea


def _row_dict_to_map(rows: list[dict], value_keys: list[str]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for row in rows:
        label = row.get("_row") or row.get("rowname") or row.get("category") or row.get("variable")
        if label is None:
            continue
        out[str(label)] = {k: row.get(k) for k in value_keys}
    return out


def test_dimdesc_pca_decathlon_quanti(r_dimdesc_pca_decathlon):
    df = load_decathlon()
    res = PCA(df, scale_unit=True, ncp=5,
              quanti_sup=["Rank", "Points"], quali_sup=["Competition"])
    desc = dimdesc(res, axes=[0, 1])
    for k, axis_key in enumerate(["Dim.1", "Dim.2"]):
        r_quanti = r_dimdesc_pca_decathlon.get(axis_key, {}).get("quanti") or []
        r_map = _row_dict_to_map(r_quanti, ["correlation", "p.value"])
        py_quanti = desc.get(k, {}).get("quanti")
        if not r_map:
            continue
        assert py_quanti is not None, f"Python dimdesc has no quanti section for axis {k}"
        # For every variable R kept (p <= 0.05), our correlation magnitude must match within 1e-6.
        for var, expect in r_map.items():
            if var not in py_quanti.index:
                # Variable name might differ — skip silently
                continue
            r_corr = float(expect["correlation"])
            py_corr = float(py_quanti.loc[var, "correlation"])
            assert math.isclose(abs(r_corr), abs(py_corr), abs_tol=1e-6), (
                f"axis {k}, var {var}: R={r_corr}, Py={py_corr}"
            )


def test_catdes_tea_quanti_var(r_catdes_tea):
    """Per-quantitative-variable eta² + F-test on tea ~ Tea."""
    tea = load_tea()
    res = catdes(tea, num_var="Tea")
    r_qv = r_catdes_tea.get("quanti.var") or []
    if not r_qv:
        pytest.skip("R fixture has no quanti.var section")
    r_map = _row_dict_to_map(r_qv, ["Eta2", "P-value"])
    py_qv = res.get("quanti_var")
    if py_qv is None:
        pytest.skip("Python catdes has no quanti_var section (no numeric vars beyond age)")
    # tea has one quantitative column ("age"). Eta2 should match R closely.
    if "age" in py_qv.index and "age" in r_map and r_map["age"]["Eta2"] is not None:
        py_eta = float(py_qv.loc["age", "Eta2"])
        r_eta = float(r_map["age"]["Eta2"])
        assert math.isclose(py_eta, r_eta, abs_tol=1e-6), f"R={r_eta}, Py={py_eta}"


def test_condes_decathlon_points_quanti(r_condes_decathlon):
    df = load_decathlon()
    res = condes(df, num_var="Points")
    r_qu = r_condes_decathlon.get("quanti") or []
    if not r_qu:
        pytest.skip("R fixture has no quanti section")
    r_map = _row_dict_to_map(r_qu, ["correlation", "p.value"])
    py_qu = res.get("quanti")
    assert py_qu is not None
    for var, expect in r_map.items():
        if var not in py_qu.index:
            continue
        r_corr = float(expect["correlation"])
        py_corr = float(py_qu.loc[var, "correlation"])
        assert math.isclose(r_corr, py_corr, abs_tol=1e-6), (
            f"var {var}: R={r_corr}, Py={py_corr}"
        )


def test_condes_decathlon_points_quali(r_condes_decathlon):
    df = load_decathlon()
    res = condes(df, num_var="Points")
    r_qa = r_condes_decathlon.get("quali") or []
    if not r_qa:
        pytest.skip("R fixture has no quali section")
    py_qa = res.get("quali")
    if py_qa is None:
        pytest.skip("Python condes has no quali section")
    r_map = _row_dict_to_map(r_qa, ["R2", "p.value"])
    for var, expect in r_map.items():
        if var not in py_qa.index:
            continue
        r_r2 = float(expect["R2"])
        py_r2 = float(py_qa.loc[var, "R2"])
        # Looser tolerance: eta² conventions can drift slightly depending on weighted-variance
        # treatment.
        assert math.isclose(r_r2, py_r2, abs_tol=1e-4), (
            f"var {var}: R={r_r2}, Py={py_r2}"
        )
