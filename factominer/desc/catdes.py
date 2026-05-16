"""``catdes`` — describe a categorical variable by the others."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def catdes(df: pd.DataFrame, num_var: int | str, proba: float = 0.05) -> dict[str, object]:
    """Describe the categorical variable ``num_var`` by all other variables.

    Returns a dict with keys:

    - ``test_chi2``: per-categorical-variable chi-square test of independence.
    - ``category``: per-category v-test against each level of ``num_var``.
    - ``quanti_var``: per-continuous-variable eta² + F-test against ``num_var``.
    - ``quanti``: per-category mean / overall-mean / v-test for each continuous
      variable.
    """
    if isinstance(num_var, str):
        if num_var not in df.columns:
            raise KeyError(num_var)
        target = df[num_var]
    else:
        target = df.iloc[:, int(num_var)]
        num_var = df.columns[int(num_var)]
    if not isinstance(target.dtype, pd.CategoricalDtype):
        target = target.astype("category")
    others = df.drop(columns=[num_var])

    qualitatives = others.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    quantitatives = others.select_dtypes(include=[np.number]).columns.tolist()

    out: dict[str, object] = {}

    # chi² independence tests
    chi2_rows = []
    for col in qualitatives:
        tab = pd.crosstab(target, others[col])
        if tab.shape[0] < 2 or tab.shape[1] < 2:
            continue
        chi2, p, dof, _ = stats.chi2_contingency(tab.to_numpy())
        chi2_rows.append((col, chi2, dof, p))
    if chi2_rows:
        out["test_chi2"] = (
            pd.DataFrame(chi2_rows, columns=["variable", "chi2", "df", "p.value"])
            .set_index("variable")
            .sort_values("p.value")
        )

    # v-test per category × each level of target
    cat_rows = []
    n = len(df)
    for lvl in target.cat.categories:
        mask_lvl = (target == lvl).to_numpy()
        nA = int(mask_lvl.sum())
        if nA == 0 or nA == n:
            continue
        for col in qualitatives:
            series = others[col].astype("category")
            for sub_lvl in series.cat.categories:
                mask_cat = (series == sub_lvl).to_numpy()
                nB = int(mask_cat.sum())
                nAB = int((mask_lvl & mask_cat).sum())
                # Hypergeometric tail
                if nB == 0 or nB == n:
                    continue
                # FactoMineR: v.test = z = (nAB - n*pA*pB) / sqrt(n*pA*pB*(1-pA)*(1-pB)) on a multinomial
                pA = nA / n
                pB = nB / n
                expected = n * pA * pB
                var = expected * (1 - pA) * (1 - pB)
                if var <= 0:
                    continue
                v = (nAB - expected) / np.sqrt(var)
                p_cat = 2 * (1 - stats.norm.cdf(abs(v)))
                cat_rows.append((str(lvl), f"{col}={sub_lvl}", v, p_cat, nAB, nA, nB, n))
    if cat_rows:
        df_cat = pd.DataFrame(
            cat_rows,
            columns=["target_level", "category", "v.test", "p.value", "nAB", "nA", "nB", "n"],
        )
        df_cat = df_cat[df_cat["p.value"] <= proba]
        out["category"] = (
            df_cat.set_index(["target_level", "category"])
            .sort_values(["target_level", "v.test"], ascending=[True, False])
        )

    # quantitative description per category
    if quantitatives:
        qv_rows = []
        per_level_rows = []
        for col in quantitatives:
            F = others[col].to_numpy()
            codes = target.cat.codes.to_numpy()
            ss_total = float(((F - F.mean()) ** 2).sum())
            if ss_total <= 0:
                continue
            arrays = [F[codes == k] for k in range(len(target.cat.categories))]
            arrays = [a for a in arrays if len(a) > 1]
            if len(arrays) < 2:
                continue
            f_stat, p_value = stats.f_oneway(*arrays)
            ss_between = sum(len(a) * (a.mean() - F.mean()) ** 2 for a in arrays)
            eta2 = ss_between / ss_total
            qv_rows.append((col, eta2, p_value))
            for ci, lvl in enumerate(target.cat.categories):
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
                per_level_rows.append((str(lvl), col, v, mean_A, mean_all, p_cat))
        if qv_rows:
            out["quanti_var"] = (
                pd.DataFrame(qv_rows, columns=["variable", "Eta2", "p.value"])
                .set_index("variable")
                .sort_values("p.value")
            )
        if per_level_rows:
            df_pl = pd.DataFrame(
                per_level_rows,
                columns=["target_level", "variable", "v.test", "Mean.in.category", "Overall.mean", "p.value"],
            )
            df_pl = df_pl[df_pl["p.value"] <= proba]
            out["quanti"] = (
                df_pl.set_index(["target_level", "variable"])
                .sort_values(["target_level", "v.test"], ascending=[True, False])
            )

    return out
