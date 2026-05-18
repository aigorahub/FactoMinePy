"""``condes`` — describe a continuous variable by the others.

Implementation tracks R FactoMineR 2.14's ``R/condes.r`` so the output schema
and ordering match exactly:

- ``quanti``: ``correlation``, ``p.value``, ``n``.
- ``quali``: ``R2``, ``p.value``.
- ``category``: ``Estimate``, ``p.value`` (Estimate is the ``contr.sum``
  regression coefficient: ``mean(level) - mean(level means)``; p.value is
  the Pearson correlation p-value of the level's one-hot indicator with the
  target).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def condes(df: pd.DataFrame, num_var: int | str, proba: float = 0.05) -> dict[str, pd.DataFrame]:
    if isinstance(num_var, str):
        target = df[num_var]
        target_name = num_var
    else:
        target = df.iloc[:, int(num_var)]
        target_name = df.columns[int(num_var)]
    F = target.to_numpy(dtype=np.float64)
    others = df.drop(columns=[target_name])
    quantitatives = others.select_dtypes(include=[np.number]).columns.tolist()
    qualitatives = others.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    out: dict[str, pd.DataFrame] = {}

    if quantitatives:
        rows = []
        for col in quantitatives:
            x = others[col].to_numpy(dtype=np.float64)
            mask = np.isfinite(x) & np.isfinite(F)
            n_pair = int(mask.sum())
            n_var = int(np.isfinite(x).sum())
            if n_pair < 3:
                continue
            r = float(np.corrcoef(x[mask], F[mask])[0, 1])
            if not np.isfinite(r):
                continue
            if abs(r) >= 1.0:
                p = 0.0
            else:
                t = r * np.sqrt((n_pair - 2) / (1 - r**2))
                p = float(2 * stats.t.sf(abs(t), df=n_pair - 2))
            rows.append((col, r, p, n_var))
        if rows:
            df_q = pd.DataFrame(rows, columns=["variable", "correlation", "p.value", "n"]).set_index(
                "variable"
            )
            df_q = df_q[(df_q["p.value"] <= proba) & (df_q["n"] > 2)].sort_values(
                "correlation", key=lambda s: -s.abs()
            )
            if not df_q.empty:
                out["quanti"] = df_q

    if qualitatives:
        quali_rows = []
        cat_rows: list[tuple[str, float, float]] = []
        for col in qualitatives:
            series = others[col].astype("category")
            cats = list(series.cat.categories)
            codes = series.cat.codes.to_numpy()
            arrays = [F[codes == k] for k in range(len(cats))]
            keep = [a for a in arrays if len(a) > 1]
            if len(keep) < 2:
                continue
            # ANOVA R2 = SS_between / SS_total over rows where x is observed.
            obs_mask = codes >= 0
            F_obs = F[obs_mask]
            grand_mean = float(F_obs.mean())
            ss_total = float(((F_obs - grand_mean) ** 2).sum())
            if ss_total == 0:
                continue
            ss_between = sum(
                len(a) * (a.mean() - grand_mean) ** 2 for a in arrays if len(a) > 0
            )
            r2 = ss_between / ss_total
            try:
                _, p_anova = stats.f_oneway(*keep)
            except (ValueError, ZeroDivisionError):
                p_anova = np.nan
            quali_rows.append((col, r2, float(p_anova) if np.isfinite(p_anova) else float("nan")))

            # Per-level Estimate (contr.sum) + correlation-based p-value.
            level_means = np.array([a.mean() if len(a) > 0 else np.nan for a in arrays])
            present = ~np.isnan(level_means)
            mean_of_means = float(level_means[present].mean()) if present.any() else 0.0
            for ci, lvl in enumerate(cats):
                arr = arrays[ci]
                if arr.size == 0:
                    continue
                estimate = float(arr.mean() - mean_of_means)
                # Pearson correlation of one-hot indicator with F.
                indicator = (codes == ci).astype(np.float64)
                mask = np.isfinite(F) & obs_mask
                if mask.sum() < 3:
                    continue
                ind = indicator[mask]
                y = F[mask]
                if ind.std(ddof=0) == 0 or y.std(ddof=0) == 0:
                    continue
                r = float(np.corrcoef(ind, y)[0, 1])
                if not np.isfinite(r):
                    continue
                if abs(r) >= 1.0:
                    p_lvl = 0.0
                else:
                    df_t = int(mask.sum()) - 2
                    t = r * np.sqrt(df_t / (1 - r**2))
                    p_lvl = float(2 * stats.t.sf(abs(t), df=df_t))
                cat_rows.append((f"{col}={lvl}", estimate, p_lvl))
        if quali_rows:
            df_qual = pd.DataFrame(quali_rows, columns=["variable", "R2", "p.value"]).set_index(
                "variable"
            )
            df_qual = df_qual[df_qual["p.value"].fillna(1.0) <= proba].sort_values("p.value")
            if not df_qual.empty:
                out["quali"] = df_qual
        if cat_rows:
            df_cat = pd.DataFrame(cat_rows, columns=["category", "Estimate", "p.value"]).set_index(
                "category"
            )
            # R sort key: rev(order(sign(Estimate)/p.value)) — positive associations first
            # (smallest p first within positives), negatives last.
            mask = df_cat["p.value"] <= proba
            df_cat = df_cat[mask]
            if not df_cat.empty:
                with np.errstate(divide="ignore"):
                    sort_key = np.sign(df_cat["Estimate"].to_numpy()) / np.where(
                        df_cat["p.value"].to_numpy() > 0,
                        df_cat["p.value"].to_numpy(),
                        np.finfo(float).tiny,
                    )
                df_cat = df_cat.iloc[np.argsort(-sort_key, kind="stable")]
                out["category"] = df_cat

    return out
