"""Parity tests for ``reconst`` (low-rank reconstruction) and ``estim_ncp``.

``reconst`` is a deterministic linear map (coords × loadings, un-scaled), so the
reconstructed entries are held to 1e-9. Fixtures drop row names (jsonlite), so
rows align positionally; columns are matched by name. ``estim_ncp``'s criterion
curve is held to 1e-7 relative and the chosen integer ``ncp`` must match exactly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from factominer import CA, PCA, estim_ncp, reconst
from factominer.datasets import load_children, load_decathlon


def _recon_df(records: list[dict]) -> pd.DataFrame:
    """Rebuild the reconstructed table from a jsonlite list-of-records, dropping
    the ``_row`` name column; columns keep their R order/names."""
    df = pd.DataFrame(records)
    return df.drop(columns=[c for c in df.columns if str(c) == "_row"])


def test_reconst_pca(r_reconst_pca_decathlon):
    deca = load_decathlon().iloc[:, :10]
    res = PCA(deca, scale_unit=True, ncp=5)
    rec = reconst(res, ncp=2)

    r_df = _recon_df(r_reconst_pca_decathlon)
    # Align columns by name (R keeps the original event order).
    py = rec[list(r_df.columns)].to_numpy(dtype=np.float64)
    assert np.allclose(py, r_df.to_numpy(dtype=np.float64), atol=1e-9, rtol=0)


def test_reconst_ca(r_reconst_ca_children):
    ch = load_children()
    res = CA(ch, row_sup=list(range(14, 18)), col_sup=list(range(5, 8)), ncp=5)
    rec = reconst(res, ncp=2)

    r_df = _recon_df(r_reconst_ca_children)
    py = rec[list(r_df.columns)].to_numpy(dtype=np.float64)
    assert np.allclose(py, r_df.to_numpy(dtype=np.float64), atol=1e-9, rtol=0)


def test_estim_ncp_gcv(r_estim_ncp_decathlon_gcv):
    deca = load_decathlon().iloc[:, :10]
    est = estim_ncp(deca, ncp_min=0, ncp_max=6, scale=True, method="GCV")
    assert est.ncp == int(r_estim_ncp_decathlon_gcv["ncp"])
    r_crit = np.asarray(r_estim_ncp_decathlon_gcv["criterion"], dtype=np.float64)
    assert np.allclose(est.criterion, r_crit, rtol=1e-7, atol=0)


def test_estim_ncp_smooth(r_estim_ncp_decathlon_smooth):
    deca = load_decathlon().iloc[:, :10]
    est = estim_ncp(deca, ncp_min=0, ncp_max=6, scale=True, method="Smooth")
    assert est.ncp == int(r_estim_ncp_decathlon_smooth["ncp"])
    r_crit = np.asarray(r_estim_ncp_decathlon_smooth["criterion"], dtype=np.float64)
    assert np.allclose(est.criterion, r_crit, rtol=1e-7, atol=0)
