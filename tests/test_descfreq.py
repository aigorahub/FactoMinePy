"""Parity test for ``descfreq`` — describe frequency-table rows by their columns.

The R fixture is a per-row named list of matrices (significant columns × the six
descfreq statistics); jsonlite keeps the significant column name as ``_row``. We
check, per described row, that the set of significant columns matches R and that
each statistic matches: the percentage / frequency columns exactly, the
hypergeometric ``p.value`` to 1e-5 relative, and ``v.test`` to 1e-6.
"""

from __future__ import annotations

import numpy as np

from factominer import descfreq
from factominer.datasets import load_children

_EXACT = ["Intern %", "glob %", "Intern freq", "Glob freq "]


def test_descfreq_children(r_descfreq_children):
    ch = load_children().iloc[:14, :5]
    res = descfreq(ch, proba=0.05)

    # Same set of rows that have at least one significant column.
    assert set(res.keys()) == set(r_descfreq_children.keys())

    for row_lab, records in r_descfreq_children.items():
        py = res[row_lab]
        r_by_col = {str(rec["_row"]): rec for rec in records}
        assert set(py.index) == set(r_by_col), f"significant columns mismatch on row {row_lab!r}"
        for col, rec in r_by_col.items():
            for stat in _EXACT:
                assert np.isclose(py.loc[col, stat], rec[stat], atol=1e-9, rtol=0), (
                    f"{row_lab}/{col} {stat}"
                )
            assert np.isclose(py.loc[col, "p.value"], rec["p.value"], rtol=1e-5, atol=1e-12), (
                f"{row_lab}/{col} p.value"
            )
            assert np.isclose(py.loc[col, "v.test"], rec["v.test"], atol=1e-6, rtol=0), (
                f"{row_lab}/{col} v.test"
            )
