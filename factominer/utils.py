"""Utility exports: ``svd_triplet`` and ``tab_disjonctif``.

These mirror the like-named FactoMineR primitives:

- :func:`svd_triplet` — the row/column-weighted SVD that underlies every factor
  method (R ``svd.triplet``). Returns the singular values and the *un-whitened*
  left/right vectors on the original scales, with R's ``sign(colSums(V))``
  orientation.
- :func:`tab_disjonctif` — the disjunctive (indicator / one-hot) coding of a
  categorical table (R ``tab.disjonctif``), including R's ``y``/``n``/``Y``/``N``
  column-naming rule.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

from ._result import SVD


def svd_triplet(
    X: np.ndarray | pd.DataFrame,
    row_w: np.ndarray | None = None,
    col_w: np.ndarray | None = None,
    ncp: int | None = None,
) -> SVD:
    """Weighted SVD of ``X`` (R ``svd.triplet``).

    Decomposes ``diag(sqrt(row_w)) X diag(sqrt(col_w))`` and returns an
    :class:`~factominer._result.SVD` with the singular values ``vs`` and the
    un-whitened left/right vectors ``U`` (``= U_tilde/sqrt(row_w)``) and ``V``
    (``= V_tilde/sqrt(col_w)``). ``row_w`` is normalized to sum to 1; the axis
    orientation follows R's ``sign(colSums(V))`` (only applied when ``ncp>1``).
    """
    A = np.asarray(X, dtype=np.float64)
    n, p = A.shape
    row_w = np.full(n, 1.0 / n) if row_w is None else np.asarray(row_w, dtype=np.float64)
    col_w = np.ones(p) if col_w is None else np.asarray(col_w, dtype=np.float64)
    ncp = min(np.inf if ncp is None else ncp, n - 1, p)
    ncp = int(ncp)
    row_w = row_w / row_w.sum()

    sqrt_row = np.sqrt(row_w)
    sqrt_col = np.sqrt(col_w)
    Y = (A * sqrt_col[None, :]) * sqrt_row[:, None]
    U_full, d_full, Vt_full = np.linalg.svd(Y, full_matrices=False)
    # R returns the full retained singular spectrum (length min(p, n-1)) but only
    # ncp singular vectors.
    vs = d_full[: min(p, n - 1)].copy()
    U = U_full[:, :ncp].copy()
    V = Vt_full[:ncp].T.copy()
    if ncp > 1:
        mult = np.sign(V.sum(axis=0))
        mult[mult == 0] = 1.0
        U = U * mult[None, :]
        V = V * mult[None, :]
    U = U / sqrt_row[:, None]
    V = V / sqrt_col[:, None]
    # R scales the singular vectors of (near-)zero singular values by the value.
    num = np.where(vs[:ncp] < 1e-15)[0]
    if num.size:
        U[:, num] = U[:, num] * vs[num][None, :]
        V[:, num] = V[:, num] * vs[num][None, :]
    return SVD(vs=vs, U=U, V=V)


def tab_disjonctif(tab: pd.DataFrame) -> pd.DataFrame:
    """Disjunctive (one-hot) coding of a categorical table (R ``tab.disjonctif``).

    Each non-numeric column expands to one 0/1 column per level (levels in
    category order). A level equal to ``"y"``/``"n"``/``"Y"``/``"N"`` is renamed
    ``"<variable>.<level>"`` (R's collision rule); numeric columns are passed
    through unchanged and appended after the indicator block.
    """
    tab = pd.DataFrame(tab)
    quali = [c for c in tab.columns if not is_numeric_dtype(tab[c].dtype)]
    if not quali:
        return tab.copy()

    blocks: list[np.ndarray] = []
    labels: list[str] = []
    yn = {"y", "n", "Y", "N"}
    for c in quali:
        s = tab[c].astype("category")
        cats = list(s.cat.categories)
        codes = s.cat.codes.to_numpy()
        block = np.zeros((len(s), len(cats)), dtype=np.int64)
        seen = codes >= 0
        block[np.arange(len(s))[seen], codes[seen]] = 1
        blocks.append(block)
        for lvl in cats:
            labels.append(f"{c}.{lvl}" if str(lvl) in yn else str(lvl))

    out = pd.DataFrame(np.hstack(blocks), index=tab.index, columns=labels)
    quanti = [c for c in tab.columns if is_numeric_dtype(tab[c].dtype)]
    for c in quanti:
        out[c] = tab[c].to_numpy()
    return out
