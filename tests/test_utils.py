"""Parity tests for the utility exports ``svd_triplet`` and ``tab_disjonctif``."""

from __future__ import annotations

import numpy as np
import pandas as pd

from factominer import svd_triplet, tab_disjonctif
from factominer._sign import align_to_reference
from factominer.datasets import load_decathlon, load_tea


def _dims(records):
    df = pd.DataFrame(records)
    cols = [c for c in df.columns if str(c) != "_row"]
    return df[cols].to_numpy(dtype=np.float64)


def test_svd_triplet(r_svd_triplet_decathlon):
    X = load_decathlon().iloc[:, :10].to_numpy(dtype=np.float64)
    row_w = np.resize(np.array([1.0, 2.0, 3.0]), X.shape[0])
    col_w = np.resize(np.array([1.0, 0.5]), X.shape[1])
    s = svd_triplet(X, row_w=row_w, col_w=col_w, ncp=5)

    r_vs = np.asarray(r_svd_triplet_decathlon["vs"], dtype=np.float64)
    r_U = _dims(r_svd_triplet_decathlon["U"])
    r_V = _dims(r_svd_triplet_decathlon["V"])
    k = r_vs.size
    assert np.allclose(s.vs[:k], r_vs, atol=1e-9, rtol=0)
    # U/V are sign-dependent per axis (gauge freedom).
    assert np.allclose(align_to_reference(s.U[:, :k], r_U), r_U, atol=1e-9, rtol=0)
    assert np.allclose(align_to_reference(s.V[:, :k], r_V), r_V, atol=1e-9, rtol=0)


def test_tab_disjonctif(r_tab_disjonctif_tea):
    td = tab_disjonctif(load_tea().iloc[:, :4])
    r = pd.DataFrame(r_tab_disjonctif_tea["table"])
    r = r.drop(columns=[c for c in r.columns if str(c) == "_row"])
    # Same column set (the indicator labels) and identical 0/1 contents.
    assert set(td.columns) == set(r.columns), f"columns: py={set(td.columns)} r={set(r.columns)}"
    py = td[list(r.columns)].to_numpy(dtype=np.int64)
    assert np.array_equal(py, r.to_numpy(dtype=np.int64))
