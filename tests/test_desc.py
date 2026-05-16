"""Parity tests for dimdesc / catdes / condes against R FactoMineR fixtures.

The fixtures are produced by ``tools/refresh_r_fixtures.R`` against the
currently-installed R FactoMineR (CRAN 2.14+ in CI). Every assertion below is
keyed to that R schema; columns added in R 2.10+ (``n`` in dimdesc/condes
quanti; ``sd in category``, ``Overall sd``, ``n`` in catdes/quanti per-level)
are now checked, and the more permissive "skip-if-missing" branches have been
removed.
"""

from __future__ import annotations

import math

import pytest

from factominer import PCA, catdes, condes, dimdesc
from factominer.datasets import load_decathlon, load_tea


def _row_dict_to_map(rows: list[dict], value_keys: list[str]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    if rows is None:
        return out
    for row in rows:
        label = (
            row.get("_row")
            or row.get("rowname")
            or row.get("category")
            or row.get("variable")
        )
        if label is None:
            continue
        out[str(label)] = {k: row.get(k) for k in value_keys}
    return out


# ---------------------------------------------------------------------------
# dimdesc
# ---------------------------------------------------------------------------


def test_dimdesc_pca_decathlon_quanti(r_dimdesc_pca_decathlon):
    df = load_decathlon()
    res = PCA(df, scale_unit=True, ncp=5,
              quanti_sup=["Rank", "Points"], quali_sup=["Competition"])
    desc = dimdesc(res, axes=[0, 1])
    for k, axis_key in enumerate(["Dim.1", "Dim.2"]):
        r_quanti = r_dimdesc_pca_decathlon.get(axis_key, {}).get("quanti") or []
        r_map = _row_dict_to_map(r_quanti, ["correlation", "p.value", "n"])
        py_quanti = desc.get(k, {}).get("quanti")
        if not r_map:
            assert py_quanti is None or py_quanti.empty
            continue
        assert py_quanti is not None, f"Python dimdesc missing quanti for axis {k}"
        # column set
        assert set(py_quanti.columns) >= {"correlation", "p.value", "n"}, (
            f"axis {k}: columns {list(py_quanti.columns)}"
        )
        for var, expect in r_map.items():
            assert var in py_quanti.index, f"axis {k}: variable {var} missing"
            r_corr = float(expect["correlation"])
            py_corr = float(py_quanti.loc[var, "correlation"])
            assert math.isclose(abs(r_corr), abs(py_corr), abs_tol=1e-9), (
                f"axis {k} {var}: R={r_corr}, Py={py_corr}"
            )
            r_p = float(expect["p.value"])
            py_p = float(py_quanti.loc[var, "p.value"])
            assert math.isclose(r_p, py_p, rel_tol=1e-6, abs_tol=1e-18), (
                f"axis {k} {var}: p R={r_p}, Py={py_p}"
            )
            r_n = int(expect["n"]) if expect["n"] is not None else None
            if r_n is not None:
                py_n = int(py_quanti.loc[var, "n"])
                assert py_n == r_n, f"axis {k} {var}: n R={r_n}, Py={py_n}"


# ---------------------------------------------------------------------------
# condes
# ---------------------------------------------------------------------------


def test_condes_decathlon_points_quanti(r_condes_decathlon):
    df = load_decathlon()
    res = condes(df, num_var="Points")
    r_qu = r_condes_decathlon.get("quanti") or []
    r_map = _row_dict_to_map(r_qu, ["correlation", "p.value", "n"])
    py_qu = res.get("quanti")
    assert py_qu is not None
    assert set(py_qu.columns) >= {"correlation", "p.value", "n"}
    for var, expect in r_map.items():
        assert var in py_qu.index, f"{var} missing in Python quanti"
        r_corr = float(expect["correlation"])
        py_corr = float(py_qu.loc[var, "correlation"])
        assert math.isclose(r_corr, py_corr, abs_tol=1e-9), f"{var} corr R={r_corr} Py={py_corr}"
        r_p = float(expect["p.value"])
        py_p = float(py_qu.loc[var, "p.value"])
        assert math.isclose(r_p, py_p, rel_tol=1e-6, abs_tol=1e-18)
        if expect["n"] is not None:
            assert int(py_qu.loc[var, "n"]) == int(expect["n"])


def test_condes_decathlon_points_quali(r_condes_decathlon):
    df = load_decathlon()
    res = condes(df, num_var="Points")
    r_qa = r_condes_decathlon.get("quali") or []
    if not r_qa:
        assert res.get("quali") is None or res["quali"].empty
        pytest.skip("R fixture has no quali section for decathlon~Points at proba=0.05")
    r_map = _row_dict_to_map(r_qa, ["R2", "p.value"])
    py_qa = res.get("quali")
    assert py_qa is not None
    for var, expect in r_map.items():
        assert var in py_qa.index
        assert math.isclose(float(expect["R2"]), float(py_qa.loc[var, "R2"]), abs_tol=1e-9)
        assert math.isclose(
            float(expect["p.value"]), float(py_qa.loc[var, "p.value"]), rel_tol=1e-6, abs_tol=1e-18
        )


def test_condes_decathlon_points_category(r_condes_decathlon):
    df = load_decathlon()
    res = condes(df, num_var="Points")
    r_cat = r_condes_decathlon.get("category") or []
    if not r_cat:
        assert res.get("category") is None or res["category"].empty
        pytest.skip("R fixture has no category section at proba=0.05")
    r_map = _row_dict_to_map(r_cat, ["Estimate", "p.value"])
    py_cat = res.get("category")
    assert py_cat is not None
    assert set(py_cat.columns) >= {"Estimate", "p.value"}
    for label, expect in r_map.items():
        assert label in py_cat.index, f"{label} missing"
        assert math.isclose(
            float(expect["Estimate"]), float(py_cat.loc[label, "Estimate"]), abs_tol=1e-9
        )
        assert math.isclose(
            float(expect["p.value"]), float(py_cat.loc[label, "p.value"]), rel_tol=1e-6, abs_tol=1e-18
        )


def test_condes_tea_age_quali_and_category(r_condes_tea_age):
    """Exercise condes' quali + category branches at proba=0.20."""
    tea = load_tea()
    res = condes(tea, num_var="age", proba=0.20)

    r_qa = r_condes_tea_age.get("quali") or []
    r_map_qa = _row_dict_to_map(r_qa, ["R2", "p.value"])
    py_qa = res.get("quali")
    if r_map_qa:
        assert py_qa is not None
        for var, expect in r_map_qa.items():
            assert var in py_qa.index, f"quali missing {var}"
            assert math.isclose(float(expect["R2"]), float(py_qa.loc[var, "R2"]), abs_tol=1e-9)
            assert math.isclose(
                float(expect["p.value"]), float(py_qa.loc[var, "p.value"]),
                rel_tol=1e-5, abs_tol=1e-18,
            )

    r_cat = r_condes_tea_age.get("category") or []
    r_map_cat = _row_dict_to_map(r_cat, ["Estimate", "p.value"])
    py_cat = res.get("category")
    if r_map_cat:
        assert py_cat is not None
        for label, expect in r_map_cat.items():
            assert label in py_cat.index, f"category missing {label}"
            assert math.isclose(
                float(expect["Estimate"]), float(py_cat.loc[label, "Estimate"]), abs_tol=1e-9
            )
            assert math.isclose(
                float(expect["p.value"]), float(py_cat.loc[label, "p.value"]),
                rel_tol=1e-5, abs_tol=1e-18,
            )


def test_dimdesc_pca_decathlon_loose_proba(r_dimdesc_pca_decathlon_proba50):
    """Same PCA setup, proba=0.50 so quali and category are populated."""
    df = load_decathlon()
    res = PCA(df, scale_unit=True, ncp=5,
              quanti_sup=["Rank", "Points"], quali_sup=["Competition"])
    desc = dimdesc(res, axes=[0, 1], proba=0.50)
    for k, axis_key in enumerate(["Dim.1", "Dim.2"]):
        r_axis = r_dimdesc_pca_decathlon_proba50.get(axis_key) or {}
        py_axis = desc.get(k) or {}

        r_qa = r_axis.get("quali") or []
        r_map_qa = _row_dict_to_map(r_qa, ["R2", "p.value"])
        py_qa = py_axis.get("quali")
        if r_map_qa:
            assert py_qa is not None, f"axis {k}: Python quali missing"
            for var, expect in r_map_qa.items():
                assert var in py_qa.index, f"axis {k} quali {var} missing"
                assert math.isclose(float(expect["R2"]), float(py_qa.loc[var, "R2"]), abs_tol=1e-9)
                assert math.isclose(
                    float(expect["p.value"]), float(py_qa.loc[var, "p.value"]),
                    rel_tol=1e-5, abs_tol=1e-18,
                )

        r_cat = r_axis.get("category") or []
        r_map_cat = _row_dict_to_map(r_cat, ["Estimate", "p.value"])
        py_cat = py_axis.get("category")
        if r_map_cat:
            assert py_cat is not None, f"axis {k}: Python category missing"
            for label, expect in r_map_cat.items():
                assert label in py_cat.index, f"axis {k} category {label} missing"
                assert math.isclose(
                    float(expect["Estimate"]), float(py_cat.loc[label, "Estimate"]), abs_tol=1e-9
                )
                assert math.isclose(
                    float(expect["p.value"]), float(py_cat.loc[label, "p.value"]),
                    rel_tol=1e-5, abs_tol=1e-18,
                )


# ---------------------------------------------------------------------------
# catdes
# ---------------------------------------------------------------------------


def test_catdes_tea_test_chi2(r_catdes_tea):
    tea = load_tea()
    res = catdes(tea, num_var="Tea")
    r_chi = r_catdes_tea.get("test.chi2") or []
    r_map = _row_dict_to_map(r_chi, ["p.value", "df"])
    py_chi = res.get("test_chi2")
    if not r_map:
        assert py_chi is None
        return
    assert py_chi is not None
    assert set(py_chi.columns) >= {"p.value", "df"}
    for var, expect in r_map.items():
        assert var in py_chi.index, f"{var} missing"
        assert math.isclose(
            float(expect["p.value"]), float(py_chi.loc[var, "p.value"]), rel_tol=1e-6, abs_tol=1e-18
        )
        assert int(py_chi.loc[var, "df"]) == int(expect["df"])


def test_catdes_tea_category_schema(r_catdes_tea):
    tea = load_tea()
    res = catdes(tea, num_var="Tea")
    r_cat = r_catdes_tea.get("category") or {}
    py_cat = res.get("category") or {}
    if not r_cat:
        assert not py_cat
        return
    for lvl, rows in r_cat.items():
        py_frame = py_cat.get(str(lvl))
        if not rows:
            assert py_frame is None or py_frame.empty
            continue
        assert py_frame is not None, f"level {lvl}: Python catdes missing"
        assert set(py_frame.columns) >= {"Cla/Mod", "Mod/Cla", "Global", "p.value", "v.test"}, (
            f"level {lvl} cols: {list(py_frame.columns)}"
        )
        r_map = _row_dict_to_map(rows, ["Cla/Mod", "Mod/Cla", "Global", "p.value", "v.test"])
        for label, expect in r_map.items():
            assert label in py_frame.index, f"level {lvl}: {label} missing"
            for col, atol in [("Cla/Mod", 1e-6), ("Mod/Cla", 1e-6), ("Global", 1e-6)]:
                assert math.isclose(
                    float(expect[col]), float(py_frame.loc[label, col]), abs_tol=atol
                ), f"level {lvl} {label} {col}: R={expect[col]} Py={py_frame.loc[label, col]}"
            assert math.isclose(
                float(expect["v.test"]),
                float(py_frame.loc[label, "v.test"]),
                abs_tol=1e-6,
            ), f"level {lvl} {label}: v.test R={expect['v.test']} Py={py_frame.loc[label, 'v.test']}"
            assert math.isclose(
                float(expect["p.value"]),
                float(py_frame.loc[label, "p.value"]),
                rel_tol=1e-5,
                abs_tol=1e-18,
            ), f"level {lvl} {label}: p R={expect['p.value']} Py={py_frame.loc[label, 'p.value']}"


def test_catdes_tea_quanti_var(r_catdes_tea):
    tea = load_tea()
    res = catdes(tea, num_var="Tea")
    r_qv = r_catdes_tea.get("quanti.var") or []
    if not r_qv:
        assert res.get("quanti_var") is None
        return
    r_map = _row_dict_to_map(r_qv, ["Eta2", "P-value"])
    py_qv = res.get("quanti_var")
    assert py_qv is not None
    assert set(py_qv.columns) >= {"Eta2", "P-value"}
    for var, expect in r_map.items():
        assert var in py_qv.index, f"{var} missing"
        assert math.isclose(
            float(expect["Eta2"]), float(py_qv.loc[var, "Eta2"]), abs_tol=1e-9
        )
        assert math.isclose(
            float(expect["P-value"]),
            float(py_qv.loc[var, "P-value"]),
            rel_tol=1e-6,
            abs_tol=1e-18,
        )


def test_catdes_tea_quanti_per_level(r_catdes_tea):
    tea = load_tea()
    res = catdes(tea, num_var="Tea")
    r_qu = r_catdes_tea.get("quanti") or {}
    py_qu = res.get("quanti") or {}
    if not r_qu:
        assert not py_qu
        return
    for lvl, rows in r_qu.items():
        py_frame = py_qu.get(str(lvl))
        if not rows:
            assert py_frame is None or py_frame.empty, (
                f"level {lvl}: R has empty quanti but Python has rows"
            )
            continue
        assert py_frame is not None, f"level {lvl}: Python catdes missing quanti"
        expected_cols = {
            "v.test",
            "Mean in category",
            "Overall mean",
            "sd in category",
            "Overall sd",
            "p.value",
            "n",
        }
        assert set(py_frame.columns) >= expected_cols, (
            f"level {lvl} cols: {list(py_frame.columns)}"
        )
        r_map = _row_dict_to_map(
            rows, ["v.test", "Mean in category", "Overall mean", "sd in category", "Overall sd",
                   "p.value", "n"]
        )
        for var, expect in r_map.items():
            assert var in py_frame.index, f"level {lvl} {var} missing"
            for col, atol in [
                ("Mean in category", 1e-9),
                ("Overall mean", 1e-9),
                ("sd in category", 1e-9),
                ("Overall sd", 1e-9),
                ("v.test", 1e-6),
            ]:
                assert math.isclose(
                    float(expect[col]), float(py_frame.loc[var, col]), abs_tol=atol
                ), f"level {lvl} {var} {col}: R={expect[col]} Py={py_frame.loc[var, col]}"
            assert math.isclose(
                float(expect["p.value"]),
                float(py_frame.loc[var, "p.value"]),
                rel_tol=1e-5,
                abs_tol=1e-18,
            )
            if expect["n"] is not None:
                assert int(py_frame.loc[var, "n"]) == int(expect["n"])
