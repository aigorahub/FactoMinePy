"""``catdes`` — describe a categorical variable by the others.

Tracks R FactoMineR 2.14's ``R/catdes.r`` so the output schema and ordering
match exactly:

- ``test_chi2``: ``p.value``, ``df`` (sorted ascending by p.value).
- ``category[level]``: ``Cla/Mod``, ``Mod/Cla``, ``Global``, ``p.value``,
  ``v.test``. p.value is the two-sided hypergeometric ("mid-p") test of the
  cluster×modality cell vs the marginals; v.test is ``±qnorm(p/2)`` signed
  by direction.
- ``quanti_var``: ``Eta2``, ``P-value`` (note: capital P and hyphen — R quirk).
- ``quanti[level]``: ``v.test``, ``Mean in category``, ``Overall mean``,
  ``sd in category``, ``Overall sd``, ``p.value``, ``n``. v.test uses the
  population sd (divide by N), matching R's ``ec()`` helper, not the sample
  sd. Sorted per level by v.test descending.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def catdes(df: pd.DataFrame, num_var: int | str, proba: float = 0.05) -> dict[str, object]:
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
    target_codes = target.cat.codes.to_numpy()
    target_levels = list(target.cat.categories)

    # ---- chi² independence + per-cluster modality breakdown -----------------
    chi2_rows: list[tuple[str, float, int]] = []
    category_by_level: dict[str, list[tuple[str, float, float, float, float, float]]] = {
        str(lvl): [] for lvl in target_levels
    }
    for col in qualitatives:
        series = others[col].astype("category")
        if len(series.cat.categories) < 2 or len(target_levels) < 2:
            continue
        # contingency table: rows = target levels, cols = modality levels
        tab = pd.crosstab(target, series)
        if tab.shape[0] < 2 or tab.shape[1] < 2:
            continue
        chi2, p, dof, _ = stats.chi2_contingency(tab.to_numpy(), correction=False)
        chi2_rows.append((col, float(p), int(dof)))

        row_sums = tab.sum(axis=1).to_numpy()  # nA per target level
        col_sums = tab.sum(axis=0).to_numpy()  # nB per modality
        N = int(col_sums.sum())
        for j, lvl in enumerate(target_levels):
            nA = int(row_sums[j])
            if nA == 0 or nA == N:
                continue
            for k, mod in enumerate(series.cat.categories):
                nB = int(col_sums[k])
                if nB == 0 or nB == N:
                    continue
                nAB = int(tab.iat[j, k])
                # Two-sided hypergeometric mid-p (matches R FactoMineR catdes.r:73):
                #   left  = 2 * P(X < nAB) + P(X = nAB)
                #   right = 2 * P(X > nAB) + P(X = nAB)
                #   p     = min(left, right)
                # P(X ≤ nAB-1) uses hypergeom.cdf(nAB-1, N, nA, nB).
                #   X ~ Hypergeom(N total, nA successes, nB draws).
                rv = stats.hypergeom(N, nA, nB)
                pmf = float(rv.pmf(nAB))
                cdf_lt = float(rv.cdf(nAB - 1))  # P(X ≤ nAB-1) = P(X < nAB)
                sf_gt = float(rv.sf(nAB))  # P(X > nAB)
                left = 2 * cdf_lt + pmf
                right = 2 * sf_gt + pmf
                p_cell = min(left, right)
                p_cell = float(min(p_cell, 1.0))
                if p_cell > proba:
                    continue
                expected_prop = nB / N
                observed_prop = nAB / nA
                sign = 1.0 if observed_prop > expected_prop else -1.0
                # qnorm(p/2) is negative; v.test = -sign * qnorm(p/2) gives
                # positive for over-rep, negative for under-rep.
                z = float(stats.norm.ppf(p_cell / 2))
                v_test = -sign * z
                cla_mod = (nAB / nB) * 100.0
                mod_cla = (nAB / nA) * 100.0
                global_pct = (nB / N) * 100.0
                category_by_level[str(lvl)].append(
                    (f"{col}={mod}", cla_mod, mod_cla, global_pct, p_cell, v_test)
                )

    if chi2_rows:
        df_chi = (
            pd.DataFrame(chi2_rows, columns=["variable", "p.value", "df"])
            .set_index("variable")
            .sort_values("p.value")
        )
        df_chi = df_chi[df_chi["p.value"] <= proba]
        if not df_chi.empty:
            out["test_chi2"] = df_chi

    cat_frames = {}
    for lvl, rows in category_by_level.items():
        if not rows:
            continue
        frame = pd.DataFrame(
            rows,
            columns=["category", "Cla/Mod", "Mod/Cla", "Global", "p.value", "v.test"],
        ).set_index("category")
        # R sorts per-level by v.test descending.
        frame = frame.sort_values("v.test", ascending=False)
        cat_frames[lvl] = frame
    if cat_frames:
        out["category"] = cat_frames

    # ---- quanti.var (Eta2 + ANOVA P-value) and per-level quanti tables ------
    if quantitatives:
        qv_rows = []
        per_level_rows: dict[str, list[tuple[str, float, float, float, float, float, float, int]]] = {
            str(lvl): [] for lvl in target_levels
        }
        for col in quantitatives:
            F = others[col].to_numpy(dtype=np.float64)
            present = np.isfinite(F)
            if not present.any():
                continue
            ss_total = float(((F[present] - F[present].mean()) ** 2).sum())
            if ss_total <= 0:
                continue
            level_arrays = [F[(target_codes == k) & present] for k in range(len(target_levels))]
            keep = [a for a in level_arrays if a.size > 1]
            if len(keep) < 2:
                continue
            try:
                _, p_anova = stats.f_oneway(*keep)
            except (ValueError, ZeroDivisionError):
                p_anova = np.nan
            ss_between = sum(
                a.size * (a.mean() - F[present].mean()) ** 2 for a in level_arrays if a.size > 0
            )
            eta2 = ss_between / ss_total
            qv_rows.append((col, eta2, float(p_anova) if np.isfinite(p_anova) else float("nan")))

            # R's catdes uses population sd (sqrt(SS/N)), not sample sd.
            overall_mean = float(F[present].mean())
            overall_sd = float(np.sqrt(((F[present] - overall_mean) ** 2).mean()))
            n_present = int(present.sum())
            for j, lvl in enumerate(target_levels):
                level_mask = (target_codes == j) & present
                n_in_level_present = int(level_mask.sum())
                n_in_level_total = int((target_codes == j).sum())
                if n_in_level_present <= 0:
                    continue
                if n_in_level_total >= n_present:
                    continue
                arr = F[level_mask]
                mean_in_cat = float(arr.mean())
                sd_in_cat = float(np.sqrt(((arr - mean_in_cat) ** 2).mean()))
                if overall_sd <= 0:
                    continue
                denom = np.sqrt((n_present - n_in_level_total) / (n_present - 1)) if n_present > 1 else 0.0
                if denom <= 0:
                    continue
                v_test = (
                    (mean_in_cat - overall_mean)
                    / overall_sd
                    * np.sqrt(n_in_level_total)
                    / denom
                )
                p_lvl = float(2 * stats.norm.sf(abs(v_test)))
                if p_lvl > proba:
                    continue
                per_level_rows[str(lvl)].append(
                    (
                        col,
                        float(v_test),
                        mean_in_cat,
                        overall_mean,
                        sd_in_cat,
                        overall_sd,
                        p_lvl,
                        n_in_level_present,
                    )
                )

        if qv_rows:
            df_qv = (
                pd.DataFrame(qv_rows, columns=["variable", "Eta2", "P-value"])
                .set_index("variable")
                .sort_values("P-value")
            )
            df_qv = df_qv[df_qv["P-value"] <= proba]
            if not df_qv.empty:
                out["quanti_var"] = df_qv

        quanti_frames = {}
        for lvl, rows in per_level_rows.items():
            if not rows:
                continue
            frame = pd.DataFrame(
                rows,
                columns=[
                    "variable",
                    "v.test",
                    "Mean in category",
                    "Overall mean",
                    "sd in category",
                    "Overall sd",
                    "p.value",
                    "n",
                ],
            ).set_index("variable")
            frame = frame.sort_values("v.test", ascending=False)
            quanti_frames[lvl] = frame
        if quanti_frames:
            out["quanti"] = quanti_frames

    return out
