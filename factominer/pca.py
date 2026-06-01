"""Principal Component Analysis — FactoMineR-compatible API."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._result import SVD, Block, Result
from ._scaling import center_scale, coerce_numeric, column_indices, row_indices
from ._svd import standard_svd
from .predict import _project_scaled


def PCA(  # noqa: N802 — mirrors R's function name
    X: pd.DataFrame,
    scale_unit: bool = True,
    ncp: int = 5,
    ind_sup: list[int] | list[str] | None = None,
    quanti_sup: list[int] | list[str] | None = None,
    quali_sup: list[int] | list[str] | None = None,
    row_w: list[float] | np.ndarray | None = None,
    col_w: list[float] | np.ndarray | None = None,
    graph: bool = False,  # noqa: ARG001 — accepted for FactoMineR compatibility; we never auto-plot
) -> Result:
    """Run PCA on a quantitative table.

    Mirrors ``FactoMineR::PCA``. Returns a :class:`Result` with ``eig``, ``ind``,
    ``var``, optional ``ind_sup``, ``quanti_sup``, ``quali_sup`` blocks, and the
    underlying ``svd``.
    """
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X must be a pandas DataFrame")
    if X.shape[0] < 2:
        raise ValueError("PCA needs at least 2 rows")

    quanti_sup_idx = column_indices(X.columns, quanti_sup)
    quali_sup_idx = column_indices(X.columns, quali_sup)
    ind_sup_idx = row_indices(X.index, ind_sup)

    # Split rows
    all_row_pos = np.arange(X.shape[0])
    active_rows = np.array([i for i in all_row_pos if i not in set(ind_sup_idx)])
    sup_rows = np.array(ind_sup_idx, dtype=int)

    # Split columns
    all_col_pos = np.arange(X.shape[1])
    sup_col_idx = set(quanti_sup_idx) | set(quali_sup_idx)
    active_cols = np.array([j for j in all_col_pos if j not in sup_col_idx])
    if active_cols.size == 0:
        raise ValueError("no active quantitative columns left after removing supplementary specs")

    X_active = X.iloc[active_rows, active_cols]
    X_arr = coerce_numeric(X_active)

    n_active = X_arr.shape[0]
    if row_w is not None:
        row_w_arr = np.asarray(row_w, dtype=np.float64)
        if row_w_arr.size != X.shape[0]:
            raise ValueError("row_w must have length == nrow(X)")
        active_row_w = row_w_arr[active_rows]
        # FactoMineR normalizes the row weights to a probability vector
        # (PCA.R: row.w <- row.w/sum(row.w)); the eigenvalues live on that scale.
        active_row_w = active_row_w / active_row_w.sum()
    else:
        active_row_w = np.full(n_active, 1.0 / n_active)
    if col_w is not None:
        col_w_arr = np.asarray(col_w, dtype=np.float64)
        if col_w_arr.size != X.shape[1]:
            raise ValueError("col_w must have length == ncol(X)")
        active_col_w = col_w_arr[active_cols]
    else:
        active_col_w = np.ones(X_arr.shape[1])

    X_scaled, mean, scale = center_scale(X_arr, scale_unit=scale_unit, row_w=active_row_w)

    # FactoMineR's PCA decomposes the row-weighted centered/scaled data so that
    # eigenvalues equal the variances explained on each axis.
    n_pc = min(ncp, X_scaled.shape[0] - 1, X_scaled.shape[1])
    sqrt_rw = np.sqrt(active_row_w)
    sqrt_cw = np.sqrt(active_col_w)
    Y = (X_scaled * sqrt_rw[:, None]) * sqrt_cw[None, :]
    U_tilde, vs, V_tilde = standard_svd(Y, n_pc)
    eigenvalues = vs**2  # variance explained on each axis (kept)
    # R FactoMineR returns ALL eigenvalues in res$eig regardless of ncp; only
    # the coord/cos2/contrib blocks are truncated. Compute the full singular
    # spectrum so eig matches R's row count.
    vs_full = np.linalg.svd(Y, compute_uv=False)
    eigenvalues_full = vs_full**2
    total_inertia = float((X_scaled**2 * active_row_w[:, None] * active_col_w[None, :]).sum())

    # Individual coordinates: F = X_scaled * diag(col_w) * V / sqrt(eig) * eig ... simpler:
    # F = (X_scaled * sqrt_cw) @ V_tilde -> in standard-weight space; then divide by sqrt_rw.
    ind_coord = (U_tilde * vs[None, :]) / sqrt_rw[:, None]
    # Variable coordinates: G = sqrt(eig) * V (correlations between vars and PCs when scaled).
    var_coord = V_tilde * vs[None, :] / sqrt_cw[:, None]

    # cos² and contributions
    ind_dist2 = (X_scaled**2 * active_col_w[None, :]).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        ind_cos2 = np.where(ind_dist2[:, None] > 0, ind_coord**2 / ind_dist2[:, None], 0.0)
    ind_contrib = (active_row_w[:, None] * ind_coord**2) / np.where(
        eigenvalues[None, :] > 0, eigenvalues[None, :], 1.0
    ) * 100.0

    var_dist2 = (X_scaled**2 * active_row_w[:, None]).sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        var_cos2 = np.where(var_dist2[:, None] > 0, var_coord**2 / var_dist2[:, None], 0.0)
    var_contrib = (active_col_w[:, None] * var_coord**2) / np.where(
        eigenvalues[None, :] > 0, eigenvalues[None, :], 1.0
    ) * 100.0

    # When scale_unit, the variable coordinates equal the correlations.
    var_cor = var_coord.copy() if scale_unit else _compute_correlations(X_arr, ind_coord, active_row_w)

    # Result tables
    dim_names = [f"Dim.{i + 1}" for i in range(n_pc)]
    active_row_labels = list(X.index[active_rows])
    active_col_labels = list(X.columns[active_cols])

    eig_df = pd.DataFrame(
        {
            "eigenvalue": eigenvalues_full,
            "percentage of variance": eigenvalues_full / total_inertia * 100.0,
            "cumulative percentage of variance": np.cumsum(eigenvalues_full) / total_inertia * 100.0,
        },
        index=[f"comp {i + 1}" for i in range(eigenvalues_full.size)],
    )

    ind_block = Block(
        coord=pd.DataFrame(ind_coord, index=active_row_labels, columns=dim_names),
        cos2=pd.DataFrame(ind_cos2, index=active_row_labels, columns=dim_names),
        contrib=pd.DataFrame(ind_contrib, index=active_row_labels, columns=dim_names),
        dist=pd.Series(np.sqrt(ind_dist2), index=active_row_labels, name="dist"),
    )

    var_block = Block(
        coord=pd.DataFrame(var_coord, index=active_col_labels, columns=dim_names),
        cos2=pd.DataFrame(var_cos2, index=active_col_labels, columns=dim_names),
        contrib=pd.DataFrame(var_contrib, index=active_col_labels, columns=dim_names),
        cor=pd.DataFrame(var_cor, index=active_col_labels, columns=dim_names),
    )

    # Supplementary individuals: the same projection as predict.PCA — project the
    # (training-)scaled sup rows onto V_tilde in the sqrt(col.w)-weighted space.
    ind_sup_block = None
    if sup_rows.size:
        X_sup = X.iloc[sup_rows, active_cols].to_numpy(dtype=np.float64)
        X_sup_scaled = (X_sup - mean) / scale if scale_unit else (X_sup - mean)
        coord_sup, cos2_sup, dist_sup = _project_scaled(X_sup_scaled, active_col_w, V_tilde)
        ind_sup_block = Block(
            coord=pd.DataFrame(coord_sup, index=list(X.index[sup_rows]), columns=dim_names),
            cos2=pd.DataFrame(cos2_sup, index=list(X.index[sup_rows]), columns=dim_names),
            dist=pd.Series(dist_sup, index=list(X.index[sup_rows]), name="dist"),
        )

    # Supplementary quantitative variables
    quanti_sup_block = None
    if quanti_sup_idx:
        X_qs = X.iloc[active_rows, quanti_sup_idx].to_numpy(dtype=np.float64)
        # Center/scale supplementary quantitative columns with the active weights.
        Xqs_scaled, _, _ = center_scale(X_qs, scale_unit=scale_unit, row_w=active_row_w)
        coord_qs = _project_supplementary_vars(Xqs_scaled, U_tilde, vs, sqrt_rw)
        # cos² of supplementary quantitative variables vs each axis
        qs_dist2 = (Xqs_scaled**2 * active_row_w[:, None]).sum(axis=0)
        with np.errstate(divide="ignore", invalid="ignore"):
            cos2_qs = np.where(qs_dist2[:, None] > 0, coord_qs**2 / qs_dist2[:, None], 0.0)
        # Correlations equal the coordinates when scale_unit (FactoMineR convention)
        cor_qs = coord_qs.copy() if scale_unit else coord_qs
        quanti_sup_block = Block(
            coord=pd.DataFrame(coord_qs, index=[X.columns[j] for j in quanti_sup_idx], columns=dim_names),
            cos2=pd.DataFrame(cos2_qs, index=[X.columns[j] for j in quanti_sup_idx], columns=dim_names),
            cor=pd.DataFrame(cor_qs, index=[X.columns[j] for j in quanti_sup_idx], columns=dim_names),
        )

    # Supplementary qualitative variables — barycenters of categories
    quali_sup_block = None
    if quali_sup_idx:
        coords_list: list[pd.DataFrame] = []
        v_test_list: list[pd.DataFrame] = []
        cos2_list: list[pd.DataFrame] = []
        dist_list: list[pd.Series] = []
        eta2_rows: list[pd.DataFrame] = []
        for j in quali_sup_idx:
            col = X.iloc[active_rows, j].astype("category")
            # eta²[var, axis] = sum_c(n_c * mean_c^2) / sum_i(F_i^2)
            # (FactoMineR-style: F is mean-zero so SS_between/SS_total).
            eta2_vec = np.zeros(ind_coord.shape[1])
            for axis_k in range(ind_coord.shape[1]):
                F = ind_coord[:, axis_k]
                ss_total = float((F * F * active_row_w).sum())
                if ss_total <= 0:
                    continue
                ss_between = 0.0
                for cat in col.cat.categories:
                    m = (col == cat).to_numpy()
                    if not m.any():
                        continue
                    w = active_row_w[m]
                    wsum = float(w.sum())
                    if wsum <= 0:
                        continue
                    mean_c = float((F[m] * w).sum() / wsum)
                    ss_between += wsum * mean_c * mean_c
                eta2_vec[axis_k] = ss_between / ss_total
            eta2_rows.append(
                pd.DataFrame([eta2_vec], index=[X.columns[j]], columns=dim_names)
            )
            for cat in col.cat.categories:
                mask = (col == cat).to_numpy()
                if not mask.any():
                    continue
                w = active_row_w[mask]
                w = w / w.sum()
                centroid = (ind_coord[mask] * w[:, None]).sum(axis=0)
                # squared distance of the category in scaled space
                cat_scaled_mean = (X_scaled[mask] * w[:, None]).sum(axis=0)
                cat_dist2 = float((cat_scaled_mean**2 * active_col_w).sum())
                with np.errstate(divide="ignore", invalid="ignore"):
                    cat_cos2 = np.where(cat_dist2 > 0, centroid**2 / cat_dist2, 0.0)
                # v-test: standardized barycenter on each axis
                p = w.size / n_active
                if 0 < p < 1:
                    # FactoMineR uses sqrt((nA*(N-1))/(N - nA)) for the multiplier
                    nA = w.size
                    multiplier = np.sqrt((nA * (n_active - 1)) / (n_active - nA)) if (n_active - nA) > 0 else 0.0
                else:
                    multiplier = 0.0
                axis_std = np.sqrt(eigenvalues)
                with np.errstate(divide="ignore", invalid="ignore"):
                    v_test = np.where(axis_std > 0, centroid / axis_std * multiplier, 0.0)
                coords_list.append(pd.DataFrame([centroid], index=[f"{X.columns[j]}={cat}"], columns=dim_names))
                v_test_list.append(pd.DataFrame([v_test], index=[f"{X.columns[j]}={cat}"], columns=dim_names))
                cos2_list.append(pd.DataFrame([cat_cos2], index=[f"{X.columns[j]}={cat}"], columns=dim_names))
                dist_list.append(pd.Series([np.sqrt(cat_dist2)], index=[f"{X.columns[j]}={cat}"], name="dist"))
        if coords_list:
            quali_sup_block = Block(
                coord=pd.concat(coords_list),
                v_test=pd.concat(v_test_list),
                cos2=pd.concat(cos2_list),
                dist=pd.concat(dist_list),
                eta2=pd.concat(eta2_rows) if eta2_rows else None,
            )

    quali_sup_frame = (
        X.iloc[active_rows, quali_sup_idx].copy()
        if quali_sup_idx
        else None
    )
    quanti_sup_frame = (
        X.iloc[active_rows, quanti_sup_idx].copy()
        if quanti_sup_idx
        else None
    )
    active_frame = X.iloc[active_rows, active_cols].copy()
    return Result(
        eig=eig_df,
        svd=SVD(vs=vs_full.copy(), U=U_tilde.copy(), V=V_tilde.copy()),
        call={
            "scale_unit": scale_unit,
            "ncp": ncp,
            "ind_sup": ind_sup_idx,
            "quanti_sup": quanti_sup_idx,
            "quali_sup": quali_sup_idx,
            "row_w": active_row_w.copy(),
            "col_w": active_col_w.copy(),
            "mean": mean.copy(),
            "scale": scale.copy(),
            "n_active": n_active,
            "active_row_labels": active_row_labels,
            "active_col_labels": active_col_labels,
            "quali_sup_frame": quali_sup_frame,
            "quanti_sup_frame": quanti_sup_frame,
            "active_frame": active_frame,
        },
        ind=ind_block,
        var=var_block,
        ind_sup=ind_sup_block,
        quanti_sup=quanti_sup_block,
        quali_sup=quali_sup_block,
        method="PCA",
    )


def _compute_correlations(
    X_arr: np.ndarray,
    ind_coord: np.ndarray,
    row_w: np.ndarray,
) -> np.ndarray:
    """Weighted Pearson correlation between each column of X and each PC score."""
    p = X_arr.shape[1]
    k = ind_coord.shape[1]
    out = np.zeros((p, k))
    Xc = X_arr - (X_arr * row_w[:, None]).sum(axis=0)
    Fc = ind_coord - (ind_coord * row_w[:, None]).sum(axis=0)
    sx = np.sqrt((Xc**2 * row_w[:, None]).sum(axis=0))
    sf = np.sqrt((Fc**2 * row_w[:, None]).sum(axis=0))
    for j in range(p):
        for d in range(k):
            denom = sx[j] * sf[d]
            if denom > 0:
                out[j, d] = float((Xc[:, j] * Fc[:, d] * row_w).sum()) / denom
    return out


def _project_supplementary_vars(
    Xqs_scaled: np.ndarray,
    U_tilde: np.ndarray,
    vs: np.ndarray,
    sqrt_rw: np.ndarray,
) -> np.ndarray:
    """Project supplementary quantitative variables onto the PC axes.

    The result is the (weighted) correlation between each supplementary
    variable and each PC axis when ``scale_unit=True``.
    """
    # PC scores in the whitened space are columns of U_tilde * vs.
    # Correlation = (X_scaled' * diag(row_w) * (U_tilde * vs)) / (||X_scaled|| * ||PC||).
    # In the whitened space ||PC|| on each axis is vs[k].
    # We want the variable coordinate G_qs[j, k] = (X_qs_scaled[:, j] · F_k) weighted by row_w / vs[k]?
    # Simpler: G_qs = (X_qs_scaled.T * row_w) @ ind_coord / vs.
    # But here we only have U_tilde, vs and sqrt_rw. F_k = U_tilde[:, k] * vs[k] / sqrt_rw.
    row_w = sqrt_rw**2
    F = (U_tilde * vs[None, :]) / sqrt_rw[:, None]
    G = (Xqs_scaled.T * row_w[None, :]) @ F
    # Normalize to correlation when X_qs is centered/scaled.
    X_norm = np.sqrt((Xqs_scaled**2 * row_w[:, None]).sum(axis=0))
    F_norm = vs.copy()
    X_norm = np.where(X_norm < 1e-12, 1.0, X_norm)
    F_norm = np.where(F_norm < 1e-12, 1.0, F_norm)
    cor = G / (X_norm[:, None] * F_norm[None, :])
    return cor
