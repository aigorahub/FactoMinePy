"""``dimdesc`` — describe each PC axis by the active and supplementary variables.

R FactoMineR's ``dimdesc`` is a thin wrapper that, for each axis ``k``, calls
``condes(cbind(axis_coord, original_X), num.var=1, proba=proba)``. We do the
same so the output schema and ordering exactly match R 2.14:

- ``quanti``: ``correlation``, ``p.value``, ``n``.
- ``quali``: ``R2``, ``p.value``.
- ``category``: ``Estimate``, ``p.value`` (Estimate is contr.sum coefficient).
"""

from __future__ import annotations

import pandas as pd

from .._result import Result
from .condes import condes


def dimdesc(
    res: Result,
    axes: list[int] | None = None,
    proba: float = 0.05,
) -> dict[int, dict[str, pd.DataFrame]]:
    if res.ind is None and res.row is None:
        raise ValueError("res must contain individual or row coordinates")

    coords = res.ind.coord if res.ind is not None else res.row.coord
    axes = list(range(coords.shape[1])) if axes is None else list(axes)

    # CA has its own dimdesc branch (R dimdesc.r L6-36): describe each axis by the
    # sorted row and column coordinates (active + supplementary). MCA and the rest
    # route through the condes-based path below (R's `else` branch).
    if res.method == "CA":
        return _dimdesc_ca(res, axes)

    active_frame = res.call.get("active_frame") if isinstance(res.call, dict) else None
    quanti_sup_frame = res.call.get("quanti_sup_frame") if isinstance(res.call, dict) else None
    quali_sup_frame = res.call.get("quali_sup_frame") if isinstance(res.call, dict) else None

    parts: list[pd.DataFrame] = []
    if active_frame is not None:
        parts.append(active_frame)
    if quanti_sup_frame is not None:
        parts.append(quanti_sup_frame)
    if quali_sup_frame is not None:
        parts.append(quali_sup_frame)
    if not parts:
        raise ValueError(
            "dimdesc requires PCA's call payload (active_frame / quanti_sup_frame / "
            "quali_sup_frame) — rerun PCA so the call dict carries the source frames."
        )
    X_all = pd.concat(parts, axis=1)
    # Keep the column order: active, quanti.sup, quali.sup.

    out: dict[int, dict[str, pd.DataFrame]] = {}
    for k in axes:
        if k < 0 or k >= coords.shape[1]:
            raise IndexError(f"axis out of range: {k}")
        axis_col = coords.iloc[:, k]
        axis_name = str(axis_col.name)
        # Make a unique name to avoid collisions with existing columns.
        unique = axis_name
        i = 0
        while unique in X_all.columns:
            i += 1
            unique = f"{axis_name}__dim{i}"
        merged = pd.concat([axis_col.rename(unique), X_all], axis=1)
        out[k] = condes(merged, num_var=unique, proba=proba)
    return out


def _dimdesc_ca(res: Result, axes: list[int]) -> dict[int, dict[str, pd.DataFrame]]:
    """CA dimdesc: per axis, the row and column coordinates sorted ascending
    (active + supplementary), each a one-column ``coord`` frame."""
    row_coord = res.row.coord
    if res.row_sup is not None:
        row_coord = pd.concat([row_coord, res.row_sup.coord])
    col_coord = res.col.coord
    if res.col_sup is not None:
        col_coord = pd.concat([col_coord, res.col_sup.coord])
    n_axes = res.row.coord.shape[1]
    out: dict[int, dict[str, pd.DataFrame]] = {}
    for k in axes:
        if k < 0 or k >= n_axes:
            raise IndexError(f"axis out of range: {k}")
        out[k] = {
            "row": row_coord.iloc[:, k].sort_values().to_frame(name="coord"),
            "col": col_coord.iloc[:, k].sort_values().to_frame(name="coord"),
        }
    return out
