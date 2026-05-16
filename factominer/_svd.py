"""Shared SVD primitives for the factor-method engines.

The generalized SVD (with row and column weights) underlies CA, MCA, FAMD, MFA.
PCA is a special case with uniform weights.
"""

from __future__ import annotations

import numpy as np

from ._sign import align_signs


def standard_svd(X: np.ndarray, ncp: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """SVD of X, truncated to ``ncp`` components, sign-aligned.

    Returns ``(U, vs, V)`` such that ``X ≈ U @ diag(vs) @ V.T``. Column counts
    of U and V are min(ncp, rank).
    """
    X = np.asarray(X, dtype=np.float64)
    if X.ndim != 2:
        raise ValueError("X must be 2D")
    U_full, vs_full, Vt_full = np.linalg.svd(X, full_matrices=False)
    rank_cap = min(ncp, vs_full.size)
    U = U_full[:, :rank_cap]
    vs = vs_full[:rank_cap]
    V = Vt_full[:rank_cap].T
    U, V = align_signs(U, V)
    return U, vs, V


def generalized_svd(
    X: np.ndarray,
    row_w: np.ndarray,
    col_w: np.ndarray,
    ncp: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generalized SVD with positive row and column weights.

    Solves ``argmax`` of the bilinear form ``u' diag(row_w) X diag(col_w) v``
    subject to ``u' diag(row_w) u = 1`` and ``v' diag(col_w) v = 1``.

    Implemented as: form ``Y = diag(sqrt(row_w)) X diag(sqrt(col_w))``, do a
    standard SVD on Y, then unwhiten the singular vectors. Returns ``(U, vs, V)``
    on the *unwhitened* (original) scales. ``vs`` are the singular values of Y.
    """
    X = np.asarray(X, dtype=np.float64)
    row_w = np.asarray(row_w, dtype=np.float64).reshape(-1)
    col_w = np.asarray(col_w, dtype=np.float64).reshape(-1)
    if row_w.size != X.shape[0] or col_w.size != X.shape[1]:
        raise ValueError("weight vectors must match X's shape")
    if (row_w <= 0).any() or (col_w <= 0).any():
        raise ValueError("weights must be strictly positive")
    sqrt_row = np.sqrt(row_w)
    sqrt_col = np.sqrt(col_w)
    Y = (X * sqrt_row[:, None]) * sqrt_col[None, :]
    U_tilde, vs, V_tilde = standard_svd(Y, ncp)
    U = U_tilde / sqrt_row[:, None]
    V = V_tilde / sqrt_col[:, None]
    return U, vs, V
