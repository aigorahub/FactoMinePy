"""``descfreq`` — describe the rows of a frequency table by their columns.

Ported from R FactoMineR 2.14 ``R/descfreq.R``. The CA analogue of
:func:`catdes`: for each row of a contingency / frequency table, find the
columns whose cell count is significantly over- or under-represented relative to
the marginals, via a two-sided hypergeometric test. Returns, per row, a frame of
the significant columns sorted by descending ``v.test``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

_COLS = ["Intern %", "glob %", "Intern freq", "Glob freq ", "p.value", "v.test"]


def descfreq(
    donnee: pd.DataFrame,
    by_quali: pd.Series | list | None = None,
    proba: float = 0.05,
) -> dict[str, pd.DataFrame]:
    """Describe each row of a frequency table by its over/under-represented columns.

    ``donnee`` is a numeric frequency table (rows × columns). ``by_quali``, if
    given, first aggregates the rows by summing within each level of the factor.
    ``proba`` is the significance threshold. Returns a dict keyed by row label;
    each value is a DataFrame (significant columns × the descfreq statistics),
    sorted by descending ``v.test``. Rows with no significant column are omitted.
    """
    if by_quali is not None:
        grouper = pd.Series(list(by_quali), index=donnee.index)
        donnee = donnee.groupby(grouper, sort=True).sum()

    counts = donnee.to_numpy(dtype=np.float64)
    row_labels = list(donnee.index)
    col_labels = list(donnee.columns)
    marge_li = counts.sum(axis=1)  # row totals
    marge_col = counts.sum(axis=0)  # column totals
    total = float(counts.sum())

    out: dict[str, pd.DataFrame] = {}
    for j, row_lab in enumerate(row_labels):
        rows: list[tuple] = []
        names: list[str] = []
        for k, col_lab in enumerate(col_labels):
            cell = counts[j, k]
            mcol = marge_col[k]
            mli = marge_li[j]
            if mcol == 0 or mli == 0:
                continue
            internal = cell / mcol
            glob = mli / total
            rv = stats.hypergeom(int(round(total)), int(round(mcol)), int(round(mli)))
            # over-represented -> upper tail P(X >= cell); else lower tail P(X <= cell)
            over = internal > glob
            p = float(rv.sf(cell - 1)) * 2.0 if over else float(rv.cdf(cell)) * 2.0
            if p > 1.0:
                p = 2.0 - p
            if p >= proba:
                continue
            sign = 1.0 if over else -1.0
            v_test = sign * float(-stats.norm.ppf(p / 2.0))
            rows.append(
                (
                    cell / mli * 100.0,  # Intern %
                    mcol / total * 100.0,  # glob %
                    cell,  # Intern freq
                    mcol,  # Glob freq
                    p,  # p.value
                    v_test,  # v.test
                )
            )
            names.append(str(col_lab))
        if rows:
            df = pd.DataFrame(rows, index=names, columns=_COLS)
            df = df.sort_values("v.test", ascending=False)
            out[str(row_lab)] = df
    return out
