"""Parity tests for ``LinearModel`` / ``AovSum`` against R FactoMineR.

contr.sum (sum-to-zero) Type-III ANOVA. Checks the ``Ftest`` (SS/df/MS/F/p) and
the rebuilt-per-level ``Ttest`` (Estimate/SE/t/p, including the reconstructed
omitted levels and — for the interaction model — the full cell grid), matched by
row name, plus the ``lmResult`` scalars. SS/coefficients to 1e-6 relative,
p-values to 1e-5, df exact.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from factominer import AovSum, LinearModel
from factominer.datasets import load_poison

_FT = ["SS", "df", "MS", "F value", "Pr(>F)"]
_TT = ["Estimate", "Std. Error", "t value", "Pr(>|t|)"]


def _byrow(records):
    df = pd.DataFrame(records)
    return df.set_index([c for c in df.columns if str(c) == "_row"][0])


def _check_ftest(py: pd.DataFrame, r_records):
    r = _byrow(r_records)
    assert set(py.index) == set(r.index), "Ftest term set"
    for term in r.index:
        for col in ("SS", "df", "MS"):
            assert np.isclose(py.loc[term, col], float(r.loc[term, col]), rtol=1e-6, atol=1e-9), (
                f"Ftest {term} {col}"
            )
        if str(term) != "Residuals":  # Residuals row has NA F / p
            assert np.isclose(py.loc[term, "F value"], float(r.loc[term, "F value"]), rtol=1e-6), (
                f"Ftest {term} F"
            )
            assert np.isclose(
                py.loc[term, "Pr(>F)"], float(r.loc[term, "Pr(>F)"]), rtol=1e-5, atol=1e-12
            ), f"Ftest {term} p"


def _check_ttest(py: pd.DataFrame, r_records):
    r = _byrow(r_records)
    assert set(py.index) == set(r.index), f"Ttest level set: py={set(py.index)} r={set(r.index)}"
    for lvl in r.index:
        for col in _TT:
            assert np.isclose(
                py.loc[lvl, col], float(r.loc[lvl, col]), rtol=1e-6, atol=1e-9
            ), f"Ttest {lvl} {col}"


def test_linear_model_main(r_linear_model_poison_main):
    res = LinearModel("Time ~ Sick + Sex + Nausea", load_poison(), type="III")
    fix = r_linear_model_poison_main
    _check_ftest(res.Ftest, fix["Ftest"])
    _check_ttest(res.Ttest, fix["Ttest"])
    assert np.isclose(res.lmResult["r.squared"], float(np.ravel(fix["r.squared"])[0]), rtol=1e-6)
    assert np.isclose(res.lmResult["sigma"], float(np.ravel(fix["sigma"])[0]), rtol=1e-6)
    assert np.allclose(res.lmResult["fstatistic"], np.ravel(fix["fstatistic"]).astype(float), rtol=1e-6)
    assert np.isclose(res.lmResult["aic"], float(np.ravel(fix["aic"])[0]), rtol=1e-6)
    assert np.isclose(res.lmResult["bic"], float(np.ravel(fix["bic"])[0]), rtol=1e-6)


def test_linear_model_interaction(r_linear_model_poison_inter):
    res = LinearModel("Time ~ Sick * Sex", load_poison(), type="III")
    fix = r_linear_model_poison_inter
    _check_ftest(res.Ftest, fix["Ftest"])
    _check_ttest(res.Ttest, fix["Ttest"])


def test_aovsum_main(r_aovsum_poison_main):
    res = AovSum("Time ~ Sick + Sex + Nausea", load_poison())
    fix = r_aovsum_poison_main
    _check_ftest(res.Ftest, fix["Ftest"])
    _check_ttest(res.Ttest, fix["Ttest"])
