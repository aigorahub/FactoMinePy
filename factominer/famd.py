"""Factor Analysis of Mixed Data — FactoMineR-compatible.

Ported from R FactoMineR 2.14 ``R/FAMD.R``. FAMD is a weighted PCA on a mixed
matrix:

- quantitative columns are centered and scaled by the (population) standard
  deviation;
- each qualitative variable is expanded to an indicator (one column per
  category), then those columns are centered by their proportion and divided
  by ``sqrt(proportion)``.

The eigen-decomposition itself is delegated to :func:`factominer.PCA` with
``scale_unit=False`` (the matrix is already scaled). This module builds the
scaled matrix and post-processes the PCA variable block into the FAMD-specific
``quanti_var``, ``quali_var``, and combined ``var`` summaries.

Key conventions matched to R FactoMineR (verified against ``R/FAMD.R``):

- ``res$eig`` is truncated to ``ncp`` (FAMD.R:126), unlike PCA/CA/MCA which
  return the full spectrum.
- ``quali.var$coord`` is a FAMD-specific transform of the dummy column's PCA
  coordinate (FAMD.R:154): ``pca_var_coord / sqrt(prop) * sqrt(eig)`` — it is
  neither the raw PCA coord nor the MCA standard coord.
- ``quali.var$v.test`` uses the *raw* PCA var coordinate of the dummy column
  (FAMD.R:157), not the transformed ``quali.var$coord``.
- ``var`` (the combined summary) stores squared loadings for quantitative
  variables and eta² for qualitative variables (FAMD.R:179, 184–185).

Supplementary variables / individuals are not yet implemented; pass only
active data. See the README known-limitations section.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._result import Block, Result
from .pca import PCA


def FAMD(  # noqa: N802 — mirrors R's function name
    X: pd.DataFrame,
    ncp: int = 5,
    graph: bool = False,  # noqa: ARG001 — accepted for FactoMineR compatibility; we never auto-plot
) -> Result:
    """Run Factor Analysis of Mixed Data on a table of mixed column types.

    Mirrors ``FactoMineR::FAMD`` for the active-variable case. Numeric columns
    are treated as quantitative, everything else as qualitative.

    Returns a :class:`Result` with ``eig``, ``ind`` (individuals),
    ``quanti_var`` (continuous variables), ``quali_var`` (categories),
    ``var`` (combined squared-loading / eta² summary), and ``svd``.
    """
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X must be a pandas DataFrame")
    if X.shape[0] < 3:
        raise ValueError("FAMD needs at least 3 rows")

    from pandas.api.types import is_numeric_dtype

    num_cols = [c for c in X.columns if is_numeric_dtype(X[c].dtype)]
    fac_cols = [c for c in X.columns if c not in num_cols]
    if not num_cols:
        raise ValueError("All variables are quantitative; use PCA instead.")
    if not fac_cols:
        raise ValueError("All variables are qualitative; use MCA instead.")

    n = X.shape[0]
    rw = np.full(n, 1.0 / n)  # uniform row weights (FAMD row.w support not exposed)

    # --- quantitative block: center + scale by population sd (R's ec.tab) ---
    Q = X[num_cols].to_numpy(dtype=np.float64)
    q_center = (Q * rw[:, None]).sum(axis=0)
    Qc = Q - q_center
    q_sd = np.sqrt((Qc**2 * rw[:, None]).sum(axis=0))
    q_sd = np.where(q_sd <= 1e-16, 1.0, q_sd)  # FAMD.R:9 — guard near-zero sd
    Qs = Qc / q_sd

    # --- qualitative block: indicator, center by prop, scale by sqrt(prop) ---
    cat_labels: list[str] = []
    fac_of_cat: list[str] = []
    nlevels: list[int] = []
    codes_per_fac: list[np.ndarray] = []
    Z_blocks: list[np.ndarray] = []
    for c in fac_cols:
        col = X[c].astype("category")
        cats = list(col.cat.categories)
        codes = col.cat.codes.to_numpy()
        codes_per_fac.append(codes)
        nlevels.append(len(cats))
        Zc = np.zeros((n, len(cats)), dtype=np.float64)
        for i, code in enumerate(codes):
            if code >= 0:
                Zc[i, code] = 1.0
        Z_blocks.append(Zc)
        cat_labels.extend(str(cat) for cat in cats)
        fac_of_cat.extend([c] * len(cats))
    Z = np.concatenate(Z_blocks, axis=1)
    prop = (Z * rw[:, None]).sum(axis=0)  # proportion = n_cat / N
    Zs = (Z - prop) / np.sqrt(prop)

    # Indicator columns are labelled by bare category (R FAMD convention). If
    # that collides with a numeric column name or across factors, disambiguate
    # with the variable name so the internal PCA index stays unique.
    combined_labels = list(num_cols) + cat_labels
    if len(set(combined_labels)) != len(combined_labels):
        cat_labels = [f"{f}={c}" for f, c in zip(fac_of_cat, cat_labels, strict=True)]
        combined_labels = list(num_cols) + cat_labels

    Xcomb = np.hstack([Qs, Zs])
    Xdf = pd.DataFrame(Xcomb, index=X.index, columns=combined_labels)

    n_quanti = len(num_cols)
    n_cat = len(cat_labels)
    n_fac = len(fac_cols)
    ncp_eff = int(min(ncp, n - 1, n_quanti + n_cat - n_fac))

    # FAMD = unscaled PCA on the pre-scaled mixed matrix (FAMD.R:124).
    pca = PCA(Xdf, scale_unit=False, ncp=ncp_eff)
    dim_names = [f"Dim.{i + 1}" for i in range(ncp_eff)]

    eig = pca.eig.iloc[:ncp_eff].copy()  # FAMD.R:126 — truncate to ncp
    eig_vals = eig["eigenvalue"].to_numpy()

    # --- quanti.var: directly the PCA variable block for the numeric columns ---
    quanti_var = Block(
        coord=pca.var.coord.loc[num_cols, dim_names].copy(),
        cos2=pca.var.cos2.loc[num_cols, dim_names].copy(),
        contrib=pca.var.contrib.loc[num_cols, dim_names].copy(),
    )

    # --- quali.var: FAMD-specific transform of the dummy PCA coordinates ---
    raw_quali_coord = pca.var.coord.loc[cat_labels, dim_names].to_numpy()
    coord_quali = (raw_quali_coord / np.sqrt(prop)[:, None]) * np.sqrt(eig_vals)[None, :]

    # Category barycenters in the scaled combined space → squared distance.
    bary = np.zeros((n_cat, Xcomb.shape[1]))
    offset = 0
    for fi in range(n_fac):
        codes = codes_per_fac[fi]
        for j in range(nlevels[fi]):
            mask = codes == j
            wsum = rw[mask].sum()
            if wsum > 0:
                bary[offset + j] = (Xcomb[mask] * rw[mask][:, None]).sum(axis=0) / wsum
        offset += nlevels[fi]
    dist2 = (bary**2).sum(axis=1)

    cos2_quali = coord_quali**2 / dist2[:, None]
    contrib_quali = pca.var.contrib.loc[cat_labels, dim_names].to_numpy()

    # v.test uses the RAW PCA var coord (FAMD.R:157), scaled by (N-n)/((N-1)N).
    n_cat_count = prop * n
    nombre = (n - n_cat_count) / ((n - 1) * n)
    vtest = raw_quali_coord / np.sqrt(nombre)[:, None]

    quali_var = Block(
        coord=pd.DataFrame(coord_quali, index=cat_labels, columns=dim_names),
        cos2=pd.DataFrame(cos2_quali, index=cat_labels, columns=dim_names),
        contrib=pd.DataFrame(contrib_quali, index=cat_labels, columns=dim_names),
        v_test=pd.DataFrame(vtest, index=cat_labels, columns=dim_names),
        dist=pd.Series(np.sqrt(dist2), index=cat_labels, name="dist"),
    )

    # --- eta²: correlation ratio of each factor with each principal axis ---
    ind_coord = pca.ind.coord[dim_names].to_numpy()
    eta2 = np.zeros((n_fac, ncp_eff))
    for fi in range(n_fac):
        eta2[fi] = _eta2_per_axis(ind_coord, codes_per_fac[fi], rw)

    # --- var: combined summary (squared loadings for quanti, eta² for quali) ---
    nlev_arr = np.asarray(nlevels, dtype=np.float64)
    quali_contrib_by_fac = np.zeros((n_fac, ncp_eff))
    offset = 0
    for fi in range(n_fac):
        quali_contrib_by_fac[fi] = contrib_quali[offset : offset + nlevels[fi]].sum(axis=0)
        offset += nlevels[fi]
    var_index = list(num_cols) + list(fac_cols)
    var_block = Block(
        coord=pd.DataFrame(
            np.vstack([quanti_var.coord.to_numpy() ** 2, eta2]),
            index=var_index,
            columns=dim_names,
        ),
        cos2=pd.DataFrame(
            np.vstack([quanti_var.cos2.to_numpy() ** 2, eta2**2 / (nlev_arr[:, None] - 1)]),
            index=var_index,
            columns=dim_names,
        ),
        contrib=pd.DataFrame(
            np.vstack([quanti_var.contrib.to_numpy(), quali_contrib_by_fac]),
            index=var_index,
            columns=dim_names,
        ),
    )

    return Result(
        eig=eig,
        svd=pca.svd,
        call={
            "ncp": ncp_eff,
            "num_cols": list(num_cols),
            "fac_cols": list(fac_cols),
            "prop": prop.copy(),
            "row_w": rw.copy(),
            "active_frame": X.copy(),
        },
        ind=pca.ind,
        var=var_block,
        quanti_var=quanti_var,
        quali_var=quali_var,
        method="FAMD",
    )


def _eta2_per_axis(ind_coord: np.ndarray, codes: np.ndarray, rw: np.ndarray) -> np.ndarray:
    """Weighted correlation ratio (between-group SS / total SS) of a factor
    against each column of ``ind_coord``. ``codes`` are category codes
    (-1 for missing, excluded). Mirrors R FAMD's ``fct.eta2``."""
    ncp = ind_coord.shape[1]
    out = np.zeros(ncp)
    ok = codes >= 0
    w = rw[ok]
    w = w / w.sum()
    F = ind_coord[ok]
    grp = codes[ok]
    uniq = np.unique(grp)
    for k in range(ncp):
        y = F[:, k]
        grand = float((w * y).sum())
        d = y - grand
        sct = float((w * d * d).sum())
        if sct <= 0:
            continue
        sce = 0.0
        for g in uniq:
            m = grp == g
            wg = w[m].sum()
            mean_g = float((w[m] * y[m]).sum() / wg)
            sce += wg * (mean_g - grand) ** 2
        out[k] = sce / sct
    return out
