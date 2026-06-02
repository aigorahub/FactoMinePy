"""``RegBest`` — best-subset linear regression selection.

Ported from R FactoMineR 2.14 ``R/RegBest.r``. For each subset size, find the
subset of predictors with the smallest residual sum of squares (R's ``leaps``
branch-and-bound; reproduced here by exhaustive enumeration, which gives the same
best-per-size result), then choose the overall best model by the requested
criterion (``"r2"`` → smallest overall-F p-value, ``"Cp"`` → Mallows' Cp,
``"adjr2"`` → adjusted R²).
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

_COEF_COLS = ["Estimate", "Std. Error", "t value", "Pr(>|t|)"]


@dataclass(frozen=True)
class RegBestModel:
    """One fitted model in :class:`RegBestResult` — the best subset of its size."""

    variables: list[str]
    coefficients: pd.DataFrame  # Intercept + selected vars × [Estimate, SE, t, p]
    r_squared: float
    adj_r_squared: float
    cp: float
    fstatistic: tuple[float, int, int]  # (value, numdf, dendf)
    pvalue: float  # overall-model F-test p-value


@dataclass(frozen=True)
class RegBestResult:
    """Result of :func:`RegBest`: the best model of each size, the R²/p-value
    summary table, and the overall best model under the chosen criterion."""

    all: list[RegBestModel]
    summary: pd.DataFrame  # rows "Model with k variable(s)", cols R2 / Pvalue
    best: RegBestModel
    best_index: int  # 0-based index into ``all`` / ``summary``


def _ols_summary(
    y: np.ndarray, Xcols: np.ndarray, var_names: list[str], intercept: bool
) -> dict:
    """OLS fit + summary.lm quantities for the design ``[1 | Xcols]``."""
    n = y.shape[0]
    X = np.column_stack([np.ones(n), Xcols]) if intercept else Xcols
    p = X.shape[1]  # parameters incl. intercept
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    rss = float(resid @ resid)
    df_res = n - p
    sigma2 = rss / df_res
    xtx_inv = np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(xtx_inv) * sigma2)
    tval = beta / se
    pval = 2.0 * stats.t.sf(np.abs(tval), df_res)
    y_mean = y.mean() if intercept else 0.0
    tss = float(((y - y_mean) ** 2).sum())
    r2 = 1.0 - rss / tss
    k = p - 1 if intercept else p  # predictors
    adj_r2 = 1.0 - (1.0 - r2) * (n - 1) / (n - p)
    fval = (r2 / k) / ((1.0 - r2) / (n - p))
    f_p = float(stats.f.sf(fval, k, n - p))
    names = (["(Intercept)"] if intercept else []) + var_names
    coef = pd.DataFrame(
        np.column_stack([beta, se, tval, pval]), index=names, columns=_COEF_COLS
    )
    return {
        "rss": rss, "r2": r2, "adj_r2": adj_r2, "fstat": (fval, k, n - p),
        "pvalue": f_p, "coef": coef, "p_params": p,
    }


def RegBest(  # noqa: N802 — mirrors R's function name
    y: pd.Series | np.ndarray,
    x: pd.DataFrame,
    int: bool = True,  # noqa: A002 — mirrors R's ``int`` argument
    method: str = "r2",
    nbest: int = 1,
) -> RegBestResult:
    """Best-subset regression of ``y`` on the columns of ``x``.

    For each subset size, the lowest-RSS subset is selected; the overall best
    model is then chosen by ``method`` (``"r2"`` / ``"Cp"`` / ``"adjr2"``).
    ``x`` must be entirely numeric. Only ``nbest=1`` is supported.
    """
    if nbest != 1:
        raise NotImplementedError("RegBest currently supports nbest=1 only.")
    if method not in ("r2", "Cp", "adjr2"):
        raise ValueError("method must be 'r2', 'Cp', or 'adjr2'")
    y = np.asarray(y, dtype=np.float64)
    if not all(np.issubdtype(x[c].dtype, np.number) for c in x.columns):
        raise ValueError("All x variables must be continuous (numeric).")
    var_names = [str(c).replace(" ", ".") for c in x.columns]
    Xarr = x.to_numpy(dtype=np.float64)
    n, p = Xarr.shape

    # Full-model residual variance for Mallows' Cp.
    full = _ols_summary(y, Xarr, var_names, int)
    sigma2_full = full["rss"] / (n - full["p_params"])

    models: list[RegBestModel] = []
    for k in range(1, p + 1):
        best_rss = np.inf
        best_combo: tuple[int, ...] = ()
        for combo in combinations(range(p), k):
            s = _ols_summary(y, Xarr[:, combo], [var_names[i] for i in combo], int)
            if s["rss"] < best_rss:
                best_rss = s["rss"]
                best_combo = combo
        s = _ols_summary(y, Xarr[:, best_combo], [var_names[i] for i in best_combo], int)
        cp = s["rss"] / sigma2_full - (n - 2 * s["p_params"])
        models.append(
            RegBestModel(
                variables=[var_names[i] for i in best_combo],
                coefficients=s["coef"],
                r_squared=s["r2"],
                adj_r_squared=s["adj_r2"],
                cp=cp,
                fstatistic=s["fstat"],
                pvalue=s["pvalue"],
            )
        )

    # (``int`` is the row-name parameter, shadowing the builtin — use .item().)
    if method == "r2":
        best_index = np.argmin([m.pvalue for m in models]).item()
    elif method == "Cp":
        best_index = np.argmin([m.cp for m in models]).item()
    else:  # adjr2
        best_index = np.argmax([m.adj_r_squared for m in models]).item()

    labels = [
        f"Model with {k} variable{'s' if k > 1 else ''}" for k in range(1, p + 1)
    ]
    summary = pd.DataFrame(
        {"R2": [m.r_squared for m in models], "Pvalue": [m.pvalue for m in models]},
        index=labels,
    )
    return RegBestResult(all=models, summary=summary, best=models[best_index], best_index=best_index)
