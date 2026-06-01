"""``reconst`` + ``estim_ncp`` — low-rank reconstruction and component estimation.

Ported from R FactoMineR 2.14 ``R/reconst.R`` and ``R/estim_ncp.r``.

- :func:`reconst` rebuilds the original table from the first ``ncp`` axes of a
  fitted ``PCA`` or ``CA`` result. PCA reconstructs in the original units
  (un-scale by ``ecart.type``, re-add ``centre``); CA reconstructs the
  contingency table in the chi-square metric.
- :func:`estim_ncp` estimates the number of PCA components by generalized
  cross-validation (GCV) or the smoothing criterion, mirroring R exactly.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ._result import Result


def reconst(res: Result, ncp: int | None = None) -> pd.DataFrame:
    """Reconstruct the active table from the first ``ncp`` axes of ``res``.

    Supports ``PCA`` and ``CA`` results. With ``ncp`` equal to the model's rank
    the reconstruction reproduces the original (active) table; smaller ``ncp``
    gives the best rank-``ncp`` approximation.
    """
    if res.method == "CA":
        return _reconst_ca(res, ncp)
    if res.method != "PCA":
        raise NotImplementedError(
            f"reconst is implemented for PCA and CA results; got {res.method!r}. "
            "(MFA reconstruction needs the per-group separate-analysis scales and "
            "is only defined for all-quantitative groups; deferred.)"
        )

    n_axes = res.ind.coord.shape[1]
    ncp = n_axes if ncp is None else min(ncp, n_axes)
    if ncp < 1:
        raise ValueError("reconst needs ncp >= 1")

    coord_ind = res.ind.coord.iloc[:, :ncp].to_numpy(dtype=np.float64)
    coord_var = res.var.coord.iloc[:, :ncp].to_numpy(dtype=np.float64)
    eig = res.eig["eigenvalue"].to_numpy(dtype=np.float64)[:ncp]

    # hatX[i,j] = sum_d coord.ind[i,d] * coord.var[j,d] / sqrt(eig_d)
    hatX = coord_ind @ (coord_var / np.sqrt(eig)[None, :]).T
    scale = np.asarray(res.call["scale"], dtype=np.float64)
    centre = np.asarray(res.call["mean"], dtype=np.float64)
    hatX = hatX * scale[None, :] + centre[None, :]

    return pd.DataFrame(
        hatX,
        index=res.ind.coord.index,
        columns=res.call["active_col_labels"],
    )


def _reconst_ca(res: Result, ncp: int | None) -> pd.DataFrame:
    """CA reconstruction (R reconst.R CA branch): rebuild the contingency table
    from the chi-square decomposition. Uses the stored row/column margins and
    grand total, so the original table is not needed."""
    n_axes = res.row.coord.shape[1]
    ncp = n_axes if ncp is None else min(ncp, n_axes)
    rr = np.asarray(res.call["marge_row"], dtype=np.float64)  # row margins of P
    rc = np.asarray(res.call["marge_col"], dtype=np.float64)  # col margins of P
    total = float(res.call["N"])  # grand total = sum(X)

    if ncp > 0:
        eig = res.eig["eigenvalue"].to_numpy(dtype=np.float64)[:ncp]
        row_coord = res.row.coord.iloc[:, :ncp].to_numpy(dtype=np.float64)
        col_coord = res.col.coord.iloc[:, :ncp].to_numpy(dtype=np.float64)
        u = (row_coord * np.sqrt(rr)[:, None]) / np.sqrt(eig)[None, :]
        v = (col_coord * np.sqrt(rc)[:, None]) / np.sqrt(eig)[None, :]
        s = (u * np.sqrt(eig)[None, :]) @ v.T
        hatX = total * (s * np.sqrt(rr)[:, None] * np.sqrt(rc)[None, :] + np.outer(rr, rc))
    else:
        hatX = total * np.outer(rr, rc)

    return pd.DataFrame(hatX, index=res.row.coord.index, columns=res.col.coord.index)


@dataclass(frozen=True)
class NcpEstimate:
    """Result of :func:`estim_ncp`: the chosen ``ncp`` and the criterion curve."""

    ncp: int
    criterion: np.ndarray


def estim_ncp(
    X: pd.DataFrame,
    ncp_min: int = 0,
    ncp_max: int | None = None,
    scale: bool = True,
    method: str = "GCV",
) -> NcpEstimate:
    """Estimate the number of PCA dimensions by GCV or the smoothing criterion.

    Mirrors R ``estim_ncp``. ``method`` is ``"GCV"`` (default) or ``"Smooth"``.
    Returns the chosen ``ncp`` (the first local minimum of the criterion) and the
    criterion vector over the candidate component counts.
    """
    method = method.lower()
    from pandas.api.types import is_numeric_dtype

    pquali = 0
    if not is_numeric_dtype(X.iloc[:, 0]):
        # Categorical path: standardized disjunctive table (R uses GCV here).
        pquali = X.shape[1]
        n_orig, p_orig = X.shape
        dummies = pd.get_dummies(X.astype("category"), prefix_sep="_").to_numpy(dtype=np.float64)
        # scale() with n-1 sd, times sqrt(n/(n-1))/sqrt(p), then * sqrt(1 - colmean)
        col_mean = dummies.mean(axis=0)
        col_sd = dummies.std(axis=0, ddof=1)
        Xm = (dummies - col_mean) / col_sd * np.sqrt(n_orig / (n_orig - 1)) / np.sqrt(p_orig)
        ponder = 1.0 - (dummies / n_orig).sum(axis=0)
        Xm = Xm * np.sqrt(ponder)[None, :]
        scale = False
    else:
        Xm = X.to_numpy(dtype=np.float64)

    n, p = Xm.shape
    if ncp_max is None:
        ncp_max = X.shape[1] - pquali - 1
    ncp_max = int(min(n - 2, X.shape[1] - 1, ncp_max))

    # Centre (always) and optionally scale by the per-column sd (ddof=1).
    Xm = Xm - Xm.mean(axis=0)
    if scale:
        et = Xm.std(axis=0, ddof=1)
        Xm = Xm / et

    crit: list[float] = []
    if ncp_min == 0:
        crit.append(float(np.mean(Xm**2) * (n * p) / ((p - pquali) * (n - 1))))

    u, d, vt = np.linalg.svd(Xm, full_matrices=False)
    q_start = max(ncp_min, 1)
    rec = np.zeros_like(Xm)
    for q in range(q_start, ncp_max + 1):
        # Incremental rank-q reconstruction: add the q-th component.
        rec = rec + d[q - 1] * np.outer(u[:, q - 1], vt[q - 1, :])
        if method == "smooth":
            a = (u[:, :q] ** 2).sum(axis=1)
            b = (vt[:q, :] ** 2).sum(axis=0)
            zz = (rec - Xm) / (1.0 - 1.0 / n - a)[:, None]
            keep = (1.0 - b) > 1e-10
            sol = zz[:, keep] / (1.0 - b)[keep][None, :]
            crit.append(float(np.mean(sol**2)))
        else:  # gcv
            denom = (n - 1) * (p - pquali) - q * (n + p - pquali - q - 1)
            crit.append(float(np.mean((n * p * (Xm - rec) / denom) ** 2)))

    crit_arr = np.asarray(crit, dtype=np.float64)
    dcrit = np.diff(crit_arr)
    # R picks the first component count where the criterion stops decreasing
    # (the first local minimum); otherwise the global minimum.
    idx = int(np.argmax(dcrit > 0)) if (dcrit > 0).any() else int(np.argmin(crit_arr))
    ncp = idx + ncp_min
    return NcpEstimate(ncp=ncp, criterion=crit_arr)
