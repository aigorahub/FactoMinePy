"""``dimdesc`` — describe each PC axis by the active and supplementary variables."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from .._result import Result


def dimdesc(
    res: Result,
    axes: list[int] | None = None,
    proba: float = 0.05,
) -> dict[int, dict[str, pd.DataFrame]]:
    """Describe each requested axis by the active + supplementary variables.

    Returns a dict keyed by axis index (0-based). Each entry maps section names
    (``"quanti"``, ``"quali"``, ``"category"``) to a sorted ``DataFrame`` with
    ``correlation`` (for quantitative) or ``Estimate`` (for category), plus a
    ``p.value`` column. Variables with ``p.value > proba`` are dropped, matching
    the FactoMineR convention.
    """
    if res.ind is None and res.row is None:
        raise ValueError("res must contain individual or row coordinates")

    coords = res.ind.coord if res.ind is not None else res.row.coord
    n = coords.shape[0]
    out: dict[int, dict[str, pd.DataFrame]] = {}
    axes = list(range(coords.shape[1])) if axes is None else list(axes)

    # Variable-vs-axis correlations: PCA already has them in res.var.cor / .quanti_sup.cor.
    # When the original raw frame is stashed in res.call["raw_frame"], we use it to compute
    # qualitative-variable descriptions too.
    var_cor = _series_cor(res.var)
    quanti_sup_cor = _series_cor(res.quanti_sup)
    quali_sup_df = res.call.get("quali_sup_frame")

    for k in axes:
        if k < 0 or k >= coords.shape[1]:
            raise IndexError(f"axis out of range: {k}")
        section: dict[str, pd.DataFrame] = {}
        F = coords.iloc[:, k].to_numpy()
        quanti_rows: list[tuple[str, float, float]] = []
        if var_cor is not None:
            for var_label, r in var_cor.iloc[:, k].items():
                p = _r_to_pvalue(float(r), n)
                quanti_rows.append((str(var_label), float(r), p))
        if quanti_sup_cor is not None:
            for var_label, r in quanti_sup_cor.iloc[:, k].items():
                p = _r_to_pvalue(float(r), n)
                quanti_rows.append((str(var_label), float(r), p))
        if quanti_rows:
            df = pd.DataFrame(quanti_rows, columns=["variable", "correlation", "p.value"]).set_index("variable")
            df = df[df["p.value"] <= proba].sort_values("correlation", key=lambda s: -s.abs())
            if not df.empty:
                section["quanti"] = df

        if quali_sup_df is not None:
            quali_rows = []
            category_rows = []
            for col in quali_sup_df.columns:
                groups = quali_sup_df[col].astype("category")
                cats = list(groups.cat.categories)
                # F-test of variance between groups vs within
                arrays = [F[groups == c] for c in cats]
                f_stat, p_value = stats.f_oneway(*arrays) if all(len(a) > 1 for a in arrays) else (np.nan, np.nan)
                eta2 = _eta_squared(F, groups.cat.codes.to_numpy())
                quali_rows.append((col, eta2, p_value))
                # per-category v-test
                for c, arr in zip(cats, arrays, strict=True):
                    nA = arr.size
                    if nA <= 0 or nA >= n:
                        continue
                    mean_A = float(arr.mean())
                    mean_all = float(F.mean())
                    var_all = float(F.var(ddof=1))
                    if var_all <= 0:
                        continue
                    se = np.sqrt(var_all * (n - nA) / (nA * (n - 1)))
                    if se <= 0:
                        continue
                    v = (mean_A - mean_all) / se
                    p_cat = 2 * (1 - stats.norm.cdf(abs(v)))
                    category_rows.append((f"{col}={c}", mean_A, v, p_cat))
            if quali_rows:
                df_q = pd.DataFrame(quali_rows, columns=["variable", "R2", "p.value"]).set_index("variable")
                df_q = df_q[df_q["p.value"].fillna(1) <= proba].sort_values("R2", ascending=False)
                if not df_q.empty:
                    section["quali"] = df_q
            if category_rows:
                df_c = pd.DataFrame(
                    category_rows, columns=["category", "Estimate", "v.test", "p.value"]
                ).set_index("category")
                df_c = df_c[df_c["p.value"] <= proba].sort_values("v.test", key=lambda s: -s.abs())
                if not df_c.empty:
                    section["category"] = df_c

        out[k] = section
    return out


def _series_cor(block) -> pd.DataFrame | None:
    """Return the per-axis correlation table for a Block (cor first, coord fallback)."""
    if block is None:
        return None
    if block.cor is not None:
        return block.cor
    return block.coord


def _r_to_pvalue(r: float, n: int) -> float:
    if not np.isfinite(r):
        return float("nan")
    if abs(r) >= 1.0:
        return 0.0
    if n < 3:
        return float("nan")
    t = r * np.sqrt((n - 2) / (1 - r**2))
    return float(2 * (1 - stats.t.cdf(abs(t), df=n - 2)))


def _eta_squared(F: np.ndarray, codes: np.ndarray) -> float:
    """Between-group sum of squares / total sum of squares for a factor variable."""
    ss_total = float(((F - F.mean()) ** 2).sum())
    if ss_total == 0:
        return 0.0
    ss_between = 0.0
    for c in np.unique(codes):
        sub = F[codes == c]
        ss_between += sub.size * (sub.mean() - F.mean()) ** 2
    return ss_between / ss_total
