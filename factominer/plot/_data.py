"""Backend-agnostic plot-data extractors.

Pure functions (no matplotlib / plotly imports) that turn a fitted result into
the arrays a renderer draws. Both the matplotlib and plotly backends consume
this module so the two stay in lock-step and the genuinely-derived display
geometry has a single source of truth.

The headline function is :func:`coord_ellipse`, a faithful port of R
FactoMineR's ``coord.ellipse`` (``R/coord.ellipse.R``). The raw point/arrow
coordinates a plot draws are just slices of the already-parity-tested result
object, so they need no separate extractor; the confidence/concentration
ellipse is the one derived quantity the analysis layer does not already expose,
and R computes it with a specific parametrization (``t·scale·cos(a ± d/2)``
with ``d = acos(r)``) that is vertex-identical to neither a generic
eigenvector ellipse nor a matplotlib ``Ellipse`` patch — so we match it exactly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

# Shared categorical color palette (Matplotlib's tab10) so the matplotlib and
# plotly backends assign identical colors to habillage groups.
DEFAULT_PALETTE = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
    "#bcbd22", "#17becf",
]


def resolve_colors(n: int, habillage, quali_sup_frame=None) -> list[str]:
    """Per-point colors for a habillage grouping, shared by both backends.

    ``habillage`` may be None (single color), a column name resolved against
    ``quali_sup_frame``, or a per-row group Series/array.
    """
    if habillage is None:
        return [DEFAULT_PALETTE[0]] * n
    if isinstance(habillage, str):
        if quali_sup_frame is None or habillage not in quali_sup_frame.columns:
            return [DEFAULT_PALETTE[0]] * n
        groups = quali_sup_frame[habillage].astype("category")
    else:
        groups = pd.Series(list(habillage)).astype("category")
    levels = list(groups.cat.categories)
    palette = {lvl: DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)] for i, lvl in enumerate(levels)}
    return [palette[lvl] for lvl in groups]


def coord_ellipse(
    coords,
    groups,
    axes: tuple[int, int] = (0, 1),
    level: float = 0.95,
    npoint: int = 100,
    bary: bool = False,
) -> dict[str, np.ndarray]:
    """Per-group confidence (or concentration) ellipse coordinates.

    Faithful port of R FactoMineR ``coord.ellipse`` for the two-axis case.

    Parameters
    ----------
    coords : array-like (n, d)
        Coordinates (e.g. ``res.ind.coord``); columns selected by ``axes``.
    groups : array-like (n,)
        Group label per row (the ``habillage`` factor).
    axes : (int, int)
        0-based column indices to use (default first two).
    level : float
        Confidence level; the radius is ``sqrt(qchisq(level, 2))``.
    npoint : int
        Number of boundary points per ellipse (R default 100); the curve is
        closed (first point ≈ last).
    bary : bool
        If True, divide the covariance by the group size to get the
        concentration ellipse of the barycenter (R's ``bary=TRUE``).

    Returns
    -------
    dict
        ``{group_label: (npoint, 2) ndarray}`` in the group's categorical
        order, matching R's level ordering.
    """
    arr = np.asarray(coords, dtype=np.float64)
    x = arr[:, axes[0]]
    y = arr[:, axes[1]]
    g = pd.Series(list(groups)).astype("category")
    levels = list(g.cat.categories)

    t = float(np.sqrt(stats.chi2.ppf(level, 2)))
    a = np.linspace(0.0, 2.0 * np.pi, npoint)  # R: seq(0, 2*pi, len=npoint)

    out: dict[str, np.ndarray] = {}
    codes = g.cat.codes.to_numpy()
    for i, lev in enumerate(levels):
        mask = codes == i
        n_g = int(mask.sum())
        tx, ty = x[mask], y[mask]
        center = np.array([np.nanmean(tx), np.nanmean(ty)])
        # ddof=1, like R's cov(); zero matrix for a singleton group (R behaviour).
        cov = np.cov(np.column_stack([tx, ty]), rowvar=False) if n_g > 1 else np.zeros((2, 2))
        if bary and n_g > 0:
            cov = cov / n_g
        r = cov[0, 1]
        scale = np.sqrt(np.array([cov[0, 0], cov[1, 1]]))
        if scale[0] > 0:
            r = r / scale[0]
        if scale[1] > 0:
            r = r / scale[1]
        r = min(max(float(r), -1.0), 1.0)
        d = np.arccos(r)
        xe = t * scale[0] * np.cos(a + d / 2.0) + center[0]
        ye = t * scale[1] * np.cos(a - d / 2.0) + center[1]
        out[str(lev)] = np.column_stack([xe, ye])
    return out
