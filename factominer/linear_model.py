"""``LinearModel`` + ``AovSum`` — linear models with sum-to-zero contrasts.

Ported from R FactoMineR 2.14 ``R/LinearModel.R`` / ``R/AovSum.r``. Both fit an
OLS model with ``contr.sum`` (sum-to-zero) contrasts and report:

- ``Ftest`` — the Type-III (or Type-II) ANOVA table (``SS``, ``df``, ``MS``,
  ``F value``, ``Pr(>F)``) plus a ``Residuals`` row.
- ``Ttest`` — the coefficient table rebuilt per factor level: a k-level factor
  contributes its ``k-1`` sum contrasts plus the reconstructed omitted level
  (``Estimate = -sum``, ``SE`` from the coefficient covariance submatrix).
- ``lmResult`` — ``r.squared``, ``sigma``, ``fstatistic``, ``aic``, ``bic``.

``AovSum(formula, data)`` is ``LinearModel(..., type="III", selection="none")``
returning only ``Ftest``/``Ttest``. Type-II SS and the AIC/BIC stepwise
``selection`` are not yet implemented (``selection="none"`` only).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

_TT_COLS = ["Estimate", "Std. Error", "t value", "Pr(>|t|)"]
_FT_COLS = ["SS", "df", "MS", "F value", "Pr(>F)"]


@dataclass(frozen=True)
class LinearModelResult:
    Ftest: pd.DataFrame
    Ttest: pd.DataFrame
    lmResult: dict
    method: str = "LinearModel"


def _parse_formula(formula: str) -> tuple[str, list[str]]:
    """Parse ``y ~ a + b + a:b`` / ``y ~ a*b`` into (response, ordered terms).
    ``a*b`` expands to ``a``, ``b``, ``a:b``."""
    lhs, rhs = formula.split("~")
    response = lhs.strip()
    terms: list[str] = []
    for raw in rhs.split("+"):
        part = raw.strip()
        if "*" in part:
            facs = [f.strip() for f in part.split("*")]
            for f in facs:
                if f not in terms:
                    terms.append(f)
            terms.append(":".join(facs))
        elif ":" in part:
            inter = ":".join(f.strip() for f in part.split(":"))
            terms.append(inter)
        elif part:
            terms.append(part)
    return response, terms


def _contr_sum(k: int) -> np.ndarray:
    """R's ``contr.sum``: a ``k × (k-1)`` matrix; row i = e_i, last row = -1."""
    c = np.zeros((k, k - 1))
    for j in range(k - 1):
        c[j, j] = 1.0
    c[k - 1, :] = -1.0
    return c


def _factor_columns(codes: np.ndarray, k: int) -> np.ndarray:
    """contr.sum design columns (n × k-1) for a factor's integer codes."""
    return _contr_sum(k)[codes]


def LinearModel(  # noqa: N802 — mirrors R's function name
    formula: str,
    data: pd.DataFrame,
    type: str = "III",  # noqa: A002 — mirrors R's ``type`` argument
    selection: str = "none",
) -> LinearModelResult:
    """Fit a linear model with sum contrasts and Type-III/II ANOVA.

    ``formula`` is an R-style string (``"y ~ a + b"``, ``"y ~ a*b"``). Non-numeric
    columns are treated as factors with ``contr.sum`` coding.
    """
    if selection not in ("none", "no", None):
        raise NotImplementedError(
            "LinearModel stepwise selection (aic/bic) is not yet implemented; "
            "use selection='none'."
        )
    type = str(type)
    if type not in ("III", "3", "II", "2"):
        raise ValueError("type must be 'III'/'3' or 'II'/'2'")

    response, terms = _parse_formula(formula)
    from pandas.api.types import is_numeric_dtype

    y = data[response].to_numpy(dtype=np.float64)
    n = y.shape[0]

    # Per term, build the contr.sum design columns and remember their span.
    cols: list[np.ndarray] = [np.ones(n)]  # intercept
    term_span: dict[str, tuple[int, int]] = {}
    term_meta: dict[str, dict] = {}

    def factor_info(name: str) -> dict:
        s = data[name].astype("category")
        return {"is_factor": True, "levels": list(s.cat.categories), "codes": s.cat.codes.to_numpy()}

    for term in terms:
        start = len(cols)
        parts = term.split(":")
        if len(parts) == 1:
            name = parts[0]
            if is_numeric_dtype(data[name].dtype):
                block = data[name].to_numpy(dtype=np.float64)[:, None]
                term_meta[term] = {"kind": "num", "vars": [name]}
            else:
                fi = factor_info(name)
                block = _factor_columns(fi["codes"], len(fi["levels"]))
                term_meta[term] = {"kind": "fac", "vars": [name], "info": {name: fi}}
        else:  # interaction (two parts supported)
            a, b = parts[0], parts[1]
            a_num = is_numeric_dtype(data[a].dtype)
            b_num = is_numeric_dtype(data[b].dtype)
            info = {}
            if a_num:
                acols = data[a].to_numpy(dtype=np.float64)[:, None]
            else:
                fa = factor_info(a)
                info[a] = fa
                acols = _factor_columns(fa["codes"], len(fa["levels"]))
            if b_num:
                bcols = data[b].to_numpy(dtype=np.float64)[:, None]
            else:
                fb = factor_info(b)
                info[b] = fb
                bcols = _factor_columns(fb["codes"], len(fb["levels"]))
            # R orders interaction columns with the first factor fastest within
            # each column of the second: (j_b outer, j_a inner).
            block = np.column_stack(
                [acols[:, ja] * bcols[:, jb] for jb in range(bcols.shape[1]) for ja in range(acols.shape[1])]
            )
            term_meta[term] = {
                "kind": "int", "vars": [a, b], "a_num": a_num, "b_num": b_num,
                "info": info, "na": acols.shape[1], "nb": bcols.shape[1],
            }
        for j in range(block.shape[1]):
            cols.append(block[:, j])
        term_span[term] = (start, len(cols))

    X = np.column_stack(cols)
    p = X.shape[1]
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    rss = float(resid @ resid)
    df_res = n - p
    sigma2 = rss / df_res
    xtx_inv = np.linalg.inv(X.T @ X)
    vcov = sigma2 * xtx_inv
    se = np.sqrt(np.diag(vcov))
    tval = beta / se
    pval = 2.0 * stats.t.sf(np.abs(tval), df_res)
    test_T = np.column_stack([beta, se, tval, pval])  # raw coefficient table

    # --- Ftest: Type-III (or II) SS per term + Residuals row ----------------
    ft_rows, ft_index = [], []
    for term in terms:
        s, e = term_span[term]
        if type in ("III", "3"):
            keep = [j for j in range(p) if not (s <= j < e)]
        else:  # Type II: drop this term AND any higher-order term containing it
            drop = set(range(s, e))
            tvars = set(term.split(":"))
            for other in terms:
                ovars = set(other.split(":"))
                if other != term and tvars < ovars:
                    os_, oe_ = term_span[other]
                    drop |= set(range(os_, oe_))
            keep = [j for j in range(p) if j not in drop]
        beta_r, _, _, _ = np.linalg.lstsq(X[:, keep], y, rcond=None)
        rss_r = float(((y - X[:, keep] @ beta_r) ** 2).sum())
        ss = rss_r - rss
        df = e - s
        ms = ss / df
        f = ms / sigma2
        ft_rows.append([ss, df, ms, f, float(stats.f.sf(f, df, df_res))])
        ft_index.append(term)
    ft_rows.append([rss, df_res, rss / df_res, np.nan, np.nan])
    ft_index.append("Residuals")
    Ftest = pd.DataFrame(ft_rows, index=ft_index, columns=_FT_COLS)

    # --- Ttest: rebuild the coefficient table per factor level --------------
    tt_rows: list[list[float]] = [list(test_T[0])]  # intercept
    tt_index: list[str] = ["(Intercept)"]

    def reconstruct(indices: list[int], sign: float) -> list[float]:
        est = sign * float(test_T[indices, 0].sum())
        sd = float(np.sqrt(vcov[np.ix_(indices, indices)].sum()))
        t = est / sd
        pv = float(stats.t.sf(abs(t), df_res) * 2.0)
        return [est, sd, t, pv]

    for term in terms:
        meta = term_meta[term]
        s, e = term_span[term]
        if meta["kind"] == "num":
            tt_rows.append(list(test_T[s]))
            tt_index.append(meta["vars"][0])
        elif meta["kind"] == "fac":
            name = meta["vars"][0]
            fi = meta["info"][name]
            idx = list(range(s, e))
            for j, lvl in zip(idx, fi["levels"][:-1], strict=True):
                tt_rows.append(list(test_T[j]))
                tt_index.append(f"{name} - {lvl}")
            tt_rows.append(reconstruct(idx, -1.0))
            tt_index.append(f"{name} - {fi['levels'][-1]}")
        else:  # interaction
            _reconstruct_interaction(term, meta, term_span, test_T, vcov, df_res, tt_rows, tt_index, data)

    Ttest = pd.DataFrame(tt_rows, index=tt_index, columns=_TT_COLS)

    # --- lmResult scalars ---------------------------------------------------
    y_mean = y.mean()
    tss = float(((y - y_mean) ** 2).sum())
    r2 = 1.0 - rss / tss
    k_pred = p - 1
    fstat_val = (r2 / k_pred) / ((1.0 - r2) / df_res)
    # R's extractAIC for an lm: n*log(RSS/n) + k*edf (NOT the Gaussian loglik).
    aic = n * np.log(rss / n) + 2.0 * p
    bic = n * np.log(rss / n) + np.log(n) * p
    lm_result = {
        "r.squared": r2,
        "adj.r.squared": 1.0 - (1.0 - r2) * (n - 1) / df_res,
        "sigma": float(np.sqrt(sigma2)),
        "fstatistic": (fstat_val, k_pred, df_res),
        "aic": float(aic),
        "bic": float(bic),
    }
    return LinearModelResult(Ftest=Ftest, Ttest=Ttest, lmResult=lm_result, method="LinearModel")


def _reconstruct_interaction(term, meta, term_span, test_T, vcov, df_res, tt_rows, tt_index, data):  # noqa: PLR0913
    """Rebuild the per-cell coefficient rows of a two-way interaction (R
    LinearModel.R lines 130-189). Factor×factor reconstructs the full cell grid;
    mixed/numeric cases append the contrast block + its reconstructed last cell."""
    s, e = term_span[term]
    a, b = meta["vars"]
    na, nb = meta["na"], meta["nb"]
    a_num, b_num = meta["a_num"], meta["b_num"]

    def reconstruct(indices, sign):
        est = sign * float(test_T[indices, 0].sum())
        sd = float(np.sqrt(vcov[np.ix_(indices, indices)].sum()))
        t = est / sd
        return [est, sd, t, float(stats.t.sf(abs(t), df_res) * 2.0)]

    if not a_num and not b_num:  # factor × factor — the canonical case
        la = meta["info"][a]["levels"]
        lb = meta["info"][b]["levels"]
        # column at offset jb*na + ja  (a fastest, b slowest)
        cell: dict[tuple[int, int], list[float]] = {}
        for jb in range(nb):  # b contrast levels (0..kb-2)
            idx = [s + jb * na + ja for ja in range(na)]
            for ja in range(na):
                cell[(ja, jb)] = list(test_T[s + jb * na + ja])
            cell[(na, jb)] = reconstruct(idx, -1.0)  # last a-level for this b
        for ja in range(na):  # last b-level per a contrast: -sum across b
            idx = [s + jb * na + ja for jb in range(nb)]
            cell[(ja, nb)] = reconstruct(idx, -1.0)
        # bottom-right cell = +sum of all interaction coefficients
        cell[(na, nb)] = reconstruct(list(range(s, e)), +1.0)
        # emit in R's order: for each b-level (incl. reconstructed), all a-levels
        for jb in range(nb + 1):
            for ja in range(na + 1):
                tt_rows.append(cell[(ja, jb)])
                tt_index.append(f"{a} - {la[ja]} : {b} - {lb[jb]}")
    elif not a_num and b_num:  # factor × numeric
        la = meta["info"][a]["levels"]
        idx = list(range(s, e))
        for ja in range(na):
            tt_rows.append(list(test_T[s + ja]))
            tt_index.append(f"{a} - {la[ja]} : {b}")
        tt_rows.append(reconstruct(idx, -1.0))
        tt_index.append(f"{a} - {la[-1]} : {b}")
    elif a_num and not b_num:  # numeric × factor
        lb = meta["info"][b]["levels"]
        idx = list(range(s, e))
        for jb in range(nb):
            tt_rows.append(list(test_T[s + jb]))
            tt_index.append(f"{b} - {lb[jb]} : {a}")
        tt_rows.append(reconstruct(idx, -1.0))
        tt_index.append(f"{b} - {lb[-1]} : {a}")
    else:  # numeric × numeric
        tt_rows.append(list(test_T[s]))
        tt_index.append(f"{a} : {b}")


def AovSum(formula: str, data: pd.DataFrame) -> LinearModelResult:  # noqa: N802 — mirrors R
    """ANOVA with sum contrasts — ``LinearModel(type="III", selection="none")``
    returning only ``Ftest`` and ``Ttest`` (R's obsolete ``AovSum``)."""
    res = LinearModel(formula, data, type="III", selection="none")
    return LinearModelResult(Ftest=res.Ftest, Ttest=res.Ttest, lmResult={}, method="AovSum")
