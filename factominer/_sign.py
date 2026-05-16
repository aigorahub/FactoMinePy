"""Deterministic sign convention for SVD-based factor methods.

SVD signs are not unique — flipping the sign of column k of U and of column k of
V leaves the decomposition unchanged. Different libraries pick different
conventions; we pick one and apply it uniformly so our output is reproducible.

Convention: for each axis k, find the row index r with the largest absolute
value in U[:, k]. If U[r, k] is negative, flip the signs of column k of U and V.
"""

from __future__ import annotations

import numpy as np


def align_signs(U: np.ndarray, V: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Apply the project's sign convention to (U, V).

    Both ``U`` and ``V`` are assumed to share the same column dimension (the
    rank kept). Returns sign-aligned copies — inputs are not modified.
    """
    U = np.asarray(U, dtype=np.float64).copy()
    V = np.asarray(V, dtype=np.float64).copy()
    if U.ndim != 2 or V.ndim != 2 or U.shape[1] != V.shape[1]:
        raise ValueError("U and V must be 2D and share the second dimension")
    for k in range(U.shape[1]):
        r = int(np.argmax(np.abs(U[:, k])))
        if U[r, k] < 0:
            U[:, k] *= -1
            V[:, k] *= -1
    return U, V


def align_to_reference(values: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Sign-align ``values`` axis-wise to ``reference``.

    For each column, multiply by -1 if the dot product with the reference column
    is negative. Used to compare our output to R FactoMineR fixtures whose own
    sign convention differs.
    """
    values = np.asarray(values, dtype=np.float64).copy()
    reference = np.asarray(reference, dtype=np.float64)
    if values.shape != reference.shape:
        raise ValueError(
            f"shape mismatch: values={values.shape}, reference={reference.shape}"
        )
    for k in range(values.shape[1]):
        if float(values[:, k] @ reference[:, k]) < 0:
            values[:, k] *= -1
    return values
