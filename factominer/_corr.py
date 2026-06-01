"""Shared correlation helpers for the factor-method engines.

The MFA family computes correlations in three closely-related ways; these are
centralized here so MFA / HMFA / DMFA share one implementation rather than each
carrying its own.
"""

from __future__ import annotations

import numpy as np


def weighted_corr(
    a: np.ndarray, b: np.ndarray, w: np.ndarray | None = None
) -> float:
    """Weighted (ML / population) Pearson correlation between two vectors.

    With ``w=None`` this is the ordinary (unweighted) Pearson correlation —
    R's ``cor(a, b)``. With weights it matches
    ``cov.wt(cbind(a, b), wt, method="ML", cor=TRUE)$cor[1, 2]`` (the ``1/n`` row
    weights cancel in the unweighted case, so the two forms agree there).
    """
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if w is None:
        w = np.full(a.shape[0], 1.0 / a.shape[0])
    else:
        w = np.asarray(w, dtype=np.float64)
        w = w / w.sum()
    da = a - float((a * w).sum())
    db = b - float((b * w).sum())
    cov = float((w * da * db).sum())
    va = float((w * da * da).sum())
    vb = float((w * db * db).sum())
    return cov / np.sqrt(va * vb) if va > 0 and vb > 0 else 0.0


def corr_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Column-wise unweighted Pearson correlation matrix — entry ``[j, k]`` is
    ``cor(a[:, j], b[:, k])`` (R's ``cor(a, b)`` for matrices)."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    ac = a - a.mean(axis=0)
    bc = b - b.mean(axis=0)
    sa = np.sqrt((ac**2).sum(axis=0))
    sb = np.sqrt((bc**2).sum(axis=0))
    return (ac.T @ bc) / np.outer(sa, sb)
