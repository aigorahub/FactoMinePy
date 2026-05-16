"""Scaling utilities for the factor-method engines."""

from __future__ import annotations

import numpy as np
import pandas as pd


def coerce_numeric(X: pd.DataFrame) -> np.ndarray:
    """Return X.values as float64, raising on any non-numeric column."""
    non_numeric = [c for c in X.columns if not np.issubdtype(X[c].dtype, np.number)]
    if non_numeric:
        raise ValueError(f"non-numeric columns in X: {non_numeric}")
    return np.asarray(X.to_numpy(), dtype=np.float64)


def center_scale(
    X: np.ndarray,
    scale_unit: bool,
    row_w: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Weighted center (and optionally scale) X.

    Returns ``(X_scaled, mean, scale)``. ``scale`` is the per-column divisor
    used (1.0 when ``scale_unit=False``). Weights default to uniform.
    """
    n = X.shape[0]
    if row_w is None:
        row_w = np.full(n, 1.0 / n)
    else:
        row_w = np.asarray(row_w, dtype=np.float64)
        if row_w.shape != (n,):
            raise ValueError("row_w must have length n")
        # Normalize to a probability vector for the moments.
        row_w = row_w / row_w.sum()
    mean = (X * row_w[:, None]).sum(axis=0)
    Xc = X - mean
    if scale_unit:
        # FactoMineR uses 1/n weighted variance (not 1/(n-1)).
        var = (Xc**2 * row_w[:, None]).sum(axis=0)
        scale = np.sqrt(var)
        scale_safe = np.where(scale < 1e-12, 1.0, scale)
        Xs = Xc / scale_safe
    else:
        scale_safe = np.ones_like(mean)
        Xs = Xc
    return Xs, mean, scale_safe


def column_indices(
    cols: list[str] | pd.Index,
    spec: list[int] | list[str] | None,
) -> list[int]:
    """Normalize a column spec (None / names / positional indices) to indices."""
    if spec is None:
        return []
    out: list[int] = []
    cols_list = list(cols)
    for item in spec:
        if isinstance(item, str):
            if item not in cols_list:
                raise KeyError(f"column not found: {item}")
            out.append(cols_list.index(item))
        elif isinstance(item, (int, np.integer)):
            idx = int(item)
            if not (0 <= idx < len(cols_list)):
                raise IndexError(f"column index out of range: {idx}")
            out.append(idx)
        else:
            raise TypeError(f"column spec items must be str or int, got {type(item).__name__}")
    if len(out) != len(set(out)):
        raise ValueError(f"duplicate column spec: {spec}")
    return out


def row_indices(
    index: pd.Index,
    spec: list[int] | list[str] | None,
) -> list[int]:
    """Normalize a row spec (None / names / positional indices) to indices."""
    if spec is None:
        return []
    out: list[int] = []
    idx_list = list(index)
    for item in spec:
        if isinstance(item, str):
            if item not in idx_list:
                raise KeyError(f"row not found: {item}")
            out.append(idx_list.index(item))
        elif isinstance(item, (int, np.integer)):
            i = int(item)
            if not (0 <= i < len(idx_list)):
                raise IndexError(f"row index out of range: {i}")
            out.append(i)
        else:
            raise TypeError(f"row spec items must be str or int, got {type(item).__name__}")
    if len(out) != len(set(out)):
        raise ValueError(f"duplicate row spec: {spec}")
    return out
