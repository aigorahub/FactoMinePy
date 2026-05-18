"""Correspondence Analysis — FactoMineR-compatible API."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._result import SVD, Block, Result
from ._scaling import row_indices
from ._svd import standard_svd


def CA(  # noqa: N802 — mirrors R
    X: pd.DataFrame,
    ncp: int = 5,
    row_sup: list[int] | list[str] | None = None,
    col_sup: list[int] | list[str] | None = None,
    graph: bool = False,  # noqa: ARG001
) -> Result:
    """Run Correspondence Analysis on a contingency table.

    Mirrors ``FactoMineR::CA``.
    """
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X must be a pandas DataFrame")
    Xv = X.to_numpy(dtype=np.float64)
    if (Xv < 0).any():
        raise ValueError("CA requires non-negative counts")

    row_sup_idx = row_indices(X.index, row_sup)
    col_sup_idx = row_indices(X.columns, col_sup)

    all_row_pos = np.arange(X.shape[0])
    all_col_pos = np.arange(X.shape[1])
    active_rows = np.array([i for i in all_row_pos if i not in set(row_sup_idx)])
    active_cols = np.array([j for j in all_col_pos if j not in set(col_sup_idx)])

    A = Xv[np.ix_(active_rows, active_cols)]
    N = float(A.sum())
    if N <= 0:
        raise ValueError("active sub-table has zero total")
    P = A / N
    r = P.sum(axis=1)
    c = P.sum(axis=0)
    if (r <= 0).any() or (c <= 0).any():
        raise ValueError("CA requires strictly positive row and column margins on the active table")
    # Standardized residuals matrix S; SVD of S gives axes.
    expected = np.outer(r, c)
    S = (P - expected) / np.sqrt(expected)
    n_pc = min(ncp, min(A.shape) - 1)
    U_tilde, vs, V_tilde = standard_svd(S, n_pc)
    eigenvalues = vs**2
    # R returns all eigenvalues in res$eig (full rank, not truncated to ncp).
    vs_full = np.linalg.svd(S, compute_uv=False)
    eigenvalues_full = vs_full**2
    # CA's rank is min(I,J)-1 (centering removes one axis); drop the trailing
    # near-zero residual so the count matches FactoMineR's res$eig row count.
    rank_ca = min(A.shape) - 1
    if eigenvalues_full.size > rank_ca:
        eigenvalues_full = eigenvalues_full[:rank_ca]
        vs_full = vs_full[:rank_ca]
    total_inertia = float((S**2).sum())

    # Row / column coordinates (chi-square distance, "symmetric" rendering).
    row_coord = (U_tilde * vs[None, :]) / np.sqrt(r)[:, None]
    col_coord = (V_tilde * vs[None, :]) / np.sqrt(c)[:, None]

    # Squared distance to centroid in chi-square space
    row_dist2 = ((P / r[:, None] - c[None, :]) ** 2 / c[None, :]).sum(axis=1)
    col_dist2 = ((P / c[None, :] - r[:, None]) ** 2 / r[:, None]).sum(axis=0)

    with np.errstate(divide="ignore", invalid="ignore"):
        row_cos2 = np.where(row_dist2[:, None] > 0, row_coord**2 / row_dist2[:, None], 0.0)
        col_cos2 = np.where(col_dist2[:, None] > 0, col_coord**2 / col_dist2[:, None], 0.0)

    row_contrib = (r[:, None] * row_coord**2) / np.where(
        eigenvalues[None, :] > 0, eigenvalues[None, :], 1.0
    ) * 100.0
    col_contrib = (c[:, None] * col_coord**2) / np.where(
        eigenvalues[None, :] > 0, eigenvalues[None, :], 1.0
    ) * 100.0

    row_inertia = r * row_dist2
    col_inertia = c * col_dist2

    dim_names = [f"Dim.{i + 1}" for i in range(n_pc)]
    active_row_labels = list(X.index[active_rows])
    active_col_labels = list(X.columns[active_cols])

    eig_df = pd.DataFrame(
        {
            "eigenvalue": eigenvalues_full,
            "percentage of variance": eigenvalues_full / total_inertia * 100.0,
            "cumulative percentage of variance": np.cumsum(eigenvalues_full) / total_inertia * 100.0,
        },
        index=[f"dim {i + 1}" for i in range(eigenvalues_full.size)],
    )

    row_block = Block(
        coord=pd.DataFrame(row_coord, index=active_row_labels, columns=dim_names),
        cos2=pd.DataFrame(row_cos2, index=active_row_labels, columns=dim_names),
        contrib=pd.DataFrame(row_contrib, index=active_row_labels, columns=dim_names),
        inertia=pd.Series(row_inertia, index=active_row_labels, name="inertia"),
        dist=pd.Series(np.sqrt(row_dist2), index=active_row_labels, name="dist"),
    )
    col_block = Block(
        coord=pd.DataFrame(col_coord, index=active_col_labels, columns=dim_names),
        cos2=pd.DataFrame(col_cos2, index=active_col_labels, columns=dim_names),
        contrib=pd.DataFrame(col_contrib, index=active_col_labels, columns=dim_names),
        inertia=pd.Series(col_inertia, index=active_col_labels, name="inertia"),
        dist=pd.Series(np.sqrt(col_dist2), index=active_col_labels, name="dist"),
    )

    # Supplementary rows (project onto column-axis basis)
    row_sup_block = None
    if row_sup_idx:
        A_sup = Xv[np.ix_(np.asarray(row_sup_idx), active_cols)]
        r_sup = A_sup.sum(axis=1)
        r_sup_safe = np.where(r_sup <= 0, 1.0, r_sup)
        prof_sup = A_sup / r_sup_safe[:, None]
        # Row sup coords = (profile - c) projected on V_tilde / sqrt(c) (transition formula)
        coord_sup = ((prof_sup - c[None, :]) / np.sqrt(c)[None, :]) @ V_tilde
        dist2_sup = ((prof_sup - c[None, :]) ** 2 / c[None, :]).sum(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            cos2_sup = np.where(dist2_sup[:, None] > 0, coord_sup**2 / dist2_sup[:, None], 0.0)
        row_sup_block = Block(
            coord=pd.DataFrame(coord_sup, index=[X.index[i] for i in row_sup_idx], columns=dim_names),
            cos2=pd.DataFrame(cos2_sup, index=[X.index[i] for i in row_sup_idx], columns=dim_names),
            dist=pd.Series(np.sqrt(dist2_sup), index=[X.index[i] for i in row_sup_idx], name="dist"),
        )

    col_sup_block = None
    if col_sup_idx:
        A_sup = Xv[np.ix_(active_rows, np.asarray(col_sup_idx))]
        c_sup = A_sup.sum(axis=0)
        c_sup_safe = np.where(c_sup <= 0, 1.0, c_sup)
        prof_sup = A_sup / c_sup_safe[None, :]
        coord_sup = ((prof_sup.T - r[None, :]) / np.sqrt(r)[None, :]) @ U_tilde
        dist2_sup = ((prof_sup.T - r[None, :]) ** 2 / r[None, :]).sum(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            cos2_sup = np.where(dist2_sup[:, None] > 0, coord_sup**2 / dist2_sup[:, None], 0.0)
        col_sup_block = Block(
            coord=pd.DataFrame(coord_sup, index=[X.columns[j] for j in col_sup_idx], columns=dim_names),
            cos2=pd.DataFrame(cos2_sup, index=[X.columns[j] for j in col_sup_idx], columns=dim_names),
            dist=pd.Series(np.sqrt(dist2_sup), index=[X.columns[j] for j in col_sup_idx], name="dist"),
        )

    return Result(
        eig=eig_df,
        svd=SVD(vs=vs_full.copy(), U=U_tilde.copy(), V=V_tilde.copy()),
        call={
            "ncp": ncp,
            "row_sup": row_sup_idx,
            "col_sup": col_sup_idx,
            "N": N,
            "marge_row": r.copy(),
            "marge_col": c.copy(),
        },
        row=row_block,
        col=col_block,
        row_sup=row_sup_block,
        col_sup=col_sup_block,
        method="CA",
    )
