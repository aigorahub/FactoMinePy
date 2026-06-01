"""Parity tests for ``RegBest`` (best-subset regression) against R FactoMineR.

Fixtures predict decathlon ``Rank`` from the 10 events (non-degenerate; the
three criteria pick different best sizes). For each method we check the per-size
``R2`` / ``Pvalue`` summary, the chosen best model's ``R2``, its coefficient
table, and the selected variable set (so the best-index choice matches R).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from factominer import RegBest
from factominer.datasets import load_decathlon

_COEF_COLS = ["Estimate", "Std. Error", "t value", "Pr(>|t|)"]


def _res(method):
    deca = load_decathlon()
    return RegBest(deca["Rank"], deca.iloc[:, :10], method=method)


def _summary(records):
    df = pd.DataFrame(records)
    return df.set_index([c for c in df.columns if str(c) == "_row"][0])


@pytest.mark.parametrize(
    ("method", "fixture_name"),
    [("r2", "r_regbest_decathlon_r2"), ("Cp", "r_regbest_decathlon_cp"),
     ("adjr2", "r_regbest_decathlon_adjr2")],
)
def test_regbest(method, fixture_name, request):
    fix = request.getfixturevalue(fixture_name)
    res = _res(method)

    # Per-size R2 / Pvalue summary (same across methods; positional by size).
    r_sum = _summary(fix["summary"])
    assert np.allclose(res.summary["R2"].to_numpy(), r_sum["R2"].to_numpy(dtype=float), rtol=1e-6, atol=0)
    assert np.allclose(
        res.summary["Pvalue"].to_numpy(), r_sum["Pvalue"].to_numpy(dtype=float), rtol=1e-5, atol=1e-300
    )

    # Chosen best model: R² + variable set + coefficient table.
    assert np.isclose(res.best.r_squared, float(np.asarray(fix["best.r2"]).reshape(-1)[0]), rtol=1e-6)
    r_coef = pd.DataFrame(fix["best.coef"])
    r_coef = r_coef.set_index([c for c in r_coef.columns if str(c) == "_row"][0])
    # Same predictor set (intercept + selected vars), order-independent.
    assert set(res.best.coefficients.index) == set(r_coef.index), f"{method} variable set"
    for name in r_coef.index:
        for col in _COEF_COLS:
            assert np.isclose(
                res.best.coefficients.loc[name, col], float(r_coef.loc[name, col]), rtol=1e-6, atol=1e-9
            ), f"{method} {name} {col}"
