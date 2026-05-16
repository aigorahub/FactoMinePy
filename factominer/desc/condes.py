"""``condes`` — describe a continuous variable by the others."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def condes(df: pd.DataFrame, num_var: int | str, proba: float = 0.05) -> dict[str, pd.DataFrame]:
    """Describe the continuous variable ``num_var`` by all other variables.

    Returns a dict with keys ``"quanti"`` (Pearson correlation + p-value with
    each continuous variable), ``"quali"`` (eta² + F-test with each categorical
    variable), and ``"category"`` (per-category v-test against ``num_var``).
    """
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
    n = len(df)
    out: dict[str, pd.DataFrame] = {}

    if quantitatives:
        rows = []
        for col in quantitatives:
            x = others[col].to_numpy(dtype=np.float64)
            mask = np.isfinite(x) & np.isfinite(F)
            if mask.sum() < 3:
                continue
            r = float(np.corrcoef(x[mask], F[mask])[0, 1])
            if not np.isfinite(r) or abs(r) >= 1.0:
                p = 0.0 if abs(r) >= 1.0 else np.nan
            else:
                t = r * np.sqrt((mask.sum() - 2) / (1 - r**2))
                p = 2 * (1 - stats.t.cdf(abs(t), df=mask.sum() - 2))
            rows.append((col, r, p))
        if rows:
            df_q = pd.DataFrame(rows, columns=["variable", "correlation", "p.value"]).set_index("variable")
            df_q = df_q[df_q["p.value"] <= proba].sort_values("correlation", key=lambda s: -s.abs())
            if not df_q.empty:
                out["quanti"] = df_q

    if qualitatives:
        quali_rows = []
        cat_rows = []
        for col in qualitatives:
            series = others[col].astype("category")
            codes = series.cat.codes.to_numpy()
            arrays = [F[codes == k] for k in range(len(series.cat.categories))]
            arrays_clean = [a for a in arrays if len(a) > 1]
            if len(arrays_clean) < 2:
                continue
            f_stat, p_value = stats.f_oneway(*arrays_clean)
            ss_total = float(((F - F.mean()) ** 2).sum())
            if ss_total == 0:
                continue
            ss_between = sum(len(a) * (a.mean() - F.mean()) ** 2 for a in arrays if len(a) > 0)
            eta2 = ss_between / ss_total
            quali_rows.append((col, eta2, p_value))
            for ci, lvl in enumerate(series.cat.categories):
                mask = codes == ci
                if not mask.any():
                    continue
                nA = int(mask.sum())
                if nA == n:
                    continue
                mean_A = float(F[mask].mean())
                mean_all = float(F.mean())
                var_all = float(np.var(F, ddof=1))
                if var_all <= 0:
                    continue
                se = np.sqrt(var_all * (n - nA) / (nA * (n - 1)))
                if se <= 0:
                    continue
                v = (mean_A - mean_all) / se
                p_cat = 2 * (1 - stats.norm.cdf(abs(v)))
                cat_rows.append((f"{col}={lvl}", mean_A, mean_all, v, p_cat))
        if quali_rows:
            df_qual = pd.DataFrame(quali_rows, columns=["variable", "R2", "p.value"]).set_index("variable")
            df_qual = df_qual[df_qual["p.value"] <= proba].sort_values("R2", ascending=False)
            if not df_qual.empty:
                out["quali"] = df_qual
        if cat_rows:
            df_cat = pd.DataFrame(
                cat_rows,
                columns=["category", "Mean.in.category", "Overall.mean", "v.test", "p.value"],
            ).set_index("category")
            df_cat = df_cat[df_cat["p.value"] <= proba].sort_values("v.test", key=lambda s: -s.abs())
            if not df_cat.empty:
                out["category"] = df_cat

    return out
