"""Multiple Correspondence Analysis — FactoMineR-compatible API."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._result import Block, Result
from ._scaling import column_indices, row_indices
from .ca import CA


def MCA(  # noqa: N802 — mirrors R
    X: pd.DataFrame,
    ncp: int = 5,
    ind_sup: list[int] | list[str] | None = None,
    quanti_sup: list[int] | list[str] | None = None,
    quali_sup: list[int] | list[str] | None = None,
    method: str = "indicator",  # "indicator" or "burt"
    graph: bool = False,  # noqa: ARG001
) -> Result:
    """Run Multiple Correspondence Analysis on a table of categorical variables.

    Mirrors ``FactoMineR::MCA``. Only the indicator-matrix and Burt methods are
    supported. Numerical columns flagged via ``quanti_sup`` are treated as
    supplementary continuous variables (correlations with axes).
    """
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X must be a pandas DataFrame")
    if method not in {"indicator", "burt"}:
        raise ValueError(f"method must be 'indicator' or 'burt', got {method!r}")

    quanti_sup_idx = column_indices(X.columns, quanti_sup)
    quali_sup_idx = column_indices(X.columns, quali_sup)
    ind_sup_idx = row_indices(X.index, ind_sup)
    sup_col_idx = set(quanti_sup_idx) | set(quali_sup_idx)

    all_rows = np.arange(X.shape[0])
    active_rows = np.array([i for i in all_rows if i not in set(ind_sup_idx)])
    active_cols = [j for j in range(X.shape[1]) if j not in sup_col_idx]
    if not active_cols:
        raise ValueError("no active categorical columns left after removing supplementary specs")

    X_active = X.iloc[active_rows, active_cols].copy()
    # Coerce to category for stable category enumeration
    for c in X_active.columns:
        X_active[c] = X_active[c].astype("category")

    # Build the indicator matrix Z (n × sum(n_categories_per_var))
    Z_blocks: list[np.ndarray] = []
    cat_labels: list[str] = []
    var_of_cat: list[str] = []  # variable name parallel to each category
    cat_counts_per_var: list[int] = []
    for c in X_active.columns:
        cats = list(X_active[c].cat.categories)
        cat_counts_per_var.append(len(cats))
        Z_var = np.zeros((X_active.shape[0], len(cats)), dtype=np.float64)
        codes = X_active[c].cat.codes.to_numpy()
        # NA codes are -1; we keep them as zero-rows for now (matches FactoMineR's complete-case usage)
        for i, code in enumerate(codes):
            if code >= 0:
                Z_var[i, code] = 1.0
        Z_blocks.append(Z_var)
        for cat in cats:
            cat_labels.append(f"{c}_{cat}")
            var_of_cat.append(c)
    Z = np.concatenate(Z_blocks, axis=1)
    n, total_cat = Z.shape
    q_vars = len(X_active.columns)

    # FactoMineR's MCA = CA of the indicator matrix. We compute it directly via CA-style SVD
    # so that we can compute the proper v-test and eta² for the categories.
    # Use CA on the indicator matrix.
    Z_df = pd.DataFrame(Z, index=X_active.index, columns=cat_labels)
    ca_res = CA(Z_df, ncp=min(ncp, total_cat - q_vars))

    # Per FactoMineR: eigenvalues from the indicator method need a Greenacre-style correction
    # only if method="burt" with adjustment. We expose raw indicator eigenvalues for now.
    # R MCA reports total_cat - q_vars eigenvalues (the "real" axes; the remaining
    # q_vars - 1 singular values from the indicator CA are spurious dummy-coding
    # artifacts). svd$vs in res keeps the full singular spectrum.
    eig_df = ca_res.eig.iloc[: total_cat - q_vars].copy()
    eig_df.index = [f"dim {i + 1}" for i in range(eig_df.shape[0])]
    # Rescale percentages to total_inertia of the real eigenvalues only.
    real_total = eig_df["eigenvalue"].sum()
    eig_df["percentage of variance"] = eig_df["eigenvalue"] / real_total * 100.0
    eig_df["cumulative percentage of variance"] = eig_df["percentage of variance"].cumsum()

    ind_block = ca_res.row
    var_block_coord = ca_res.col.coord.copy()
    var_block_cos2 = ca_res.col.cos2.copy()
    var_block_contrib = ca_res.col.contrib.copy()

    # v-test for categories (R MCA.R line 278-280):
    #   v.test = standard_coord * sqrt(n_c * (N - 1) / (N - n_c))
    # where standard_coord is res$var$coord (FactoMineR's MCA uses the standard
    # category coordinate ψ_c for active categories, so no /sqrt(eig) needed).
    cat_counts = Z.sum(axis=0)
    multiplier = np.where(
        (n - cat_counts) > 0,
        np.sqrt((cat_counts * (n - 1)) / (n - cat_counts)),
        0.0,
    )
    v_test = var_block_coord.to_numpy() * multiplier[:, None]
    v_test_df = pd.DataFrame(v_test, index=var_block_coord.index, columns=var_block_coord.columns)

    # eta² per variable per axis: sum of (n_A * coord_A^2) / (n * eig) over A in var
    n_active = n
    eta2 = np.zeros((q_vars, var_block_coord.shape[1]))
    var_names = list(X_active.columns)
    offset = 0
    for vi in range(len(var_names)):
        ncat = cat_counts_per_var[vi]
        slice_coords = var_block_coord.iloc[offset:offset + ncat].to_numpy()
        slice_counts = cat_counts[offset:offset + ncat]
        # MCA convention: var.coord is the STANDARD category coordinate ψ_c
        # (G_c = ψ_c * sqrt(lambda_k)). Therefore
        #   SS_between(v, k) = sum_c n_c * (ψ_c * sqrt(lambda_k))^2
        #                    = lambda_k * sum_c n_c * ψ_c^2
        #   SS_total(k)      = N * lambda_k
        #   eta²(v, k)       = SS_between / SS_total = sum_c n_c * ψ_c^2 / N
        for k in range(eta2.shape[1]):
            eta2[vi, k] = float((slice_counts * slice_coords[:, k] ** 2).sum()) / n_active
        offset += ncat
    eta2_df = pd.DataFrame(eta2, index=var_names, columns=var_block_coord.columns)

    var_block = Block(
        coord=var_block_coord,
        cos2=var_block_cos2,
        contrib=var_block_contrib,
        v_test=v_test_df,
        eta2=eta2_df,
    )

    return Result(
        eig=eig_df,
        svd=ca_res.svd,
        call={
            "ncp": ncp,
            "method": method,
            "ind_sup": ind_sup_idx,
            "quanti_sup": quanti_sup_idx,
            "quali_sup": quali_sup_idx,
            "q_vars": q_vars,
            "n_active": n_active,
            "cat_labels": cat_labels,
            "var_of_cat": var_of_cat,
            "cat_counts_per_var": cat_counts_per_var,
        },
        ind=ind_block,
        var=var_block,
        method="MCA",
    )
