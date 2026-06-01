"""Parity tests for ``CaGalt`` (type="s") against R FactoMineR.

Deterministic blocks only (the bootstrap confidence ellipses are excluded).
``coord`` / ``cor`` are sign-dependent (the inner-PCA axis signs) so each is
sign-aligned per axis before comparison; ``eig`` / ``cos2`` / ``contrib`` are
sign-invariant. Fixtures drop row names (jsonlite), so rows align positionally
in the natural Y-row / Y-col / X-col order.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from factominer import CaGalt
from factominer._sign import align_to_reference
from factominer.datasets import load_cagalt_synth


def _mat(records: list[dict], cols: list[str]) -> np.ndarray:
    df = pd.DataFrame(records)
    return df[cols].to_numpy(dtype=np.float64)


def _dims(records: list[dict]) -> np.ndarray:
    """Pull the ``Dim.k`` columns (drop ``_row``) in index order."""
    df = pd.DataFrame(records)
    dim_cols = sorted(
        (c for c in df.columns if str(c).startswith("Dim")),
        key=lambda c: int(str(c).split(".")[-1]),
    )
    return df[dim_cols].to_numpy(dtype=np.float64)


def _res():
    df = load_cagalt_synth()
    return CaGalt(df.iloc[:, :6], df.iloc[:, 6:9], type="s")


def test_cagalt_eig(r_cagalt_synth_s):
    res = _res()
    r_eig = _mat(r_cagalt_synth_s["eig"], ["eigenvalue"])[:, 0]
    py = res.eig["eigenvalue"].to_numpy()[: len(r_eig)]
    assert np.allclose(py, r_eig, atol=1e-10, rtol=0)


def test_cagalt_ind(r_cagalt_synth_s):
    res = _res()
    r_coord = _dims(r_cagalt_synth_s["ind"]["coord"])
    r_cos2 = _dims(r_cagalt_synth_s["ind"]["cos2"])
    k = r_coord.shape[1]
    assert np.allclose(
        align_to_reference(res.ind.coord.to_numpy()[:, :k], r_coord), r_coord, atol=1e-9, rtol=0
    )
    assert np.allclose(res.ind.cos2.to_numpy()[:, :k], r_cos2, atol=1e-9, rtol=0)


def test_cagalt_freq(r_cagalt_synth_s):
    res = _res()
    r_coord = _dims(r_cagalt_synth_s["freq"]["coord"])
    r_cos2 = _dims(r_cagalt_synth_s["freq"]["cos2"])
    r_contrib = _dims(r_cagalt_synth_s["freq"]["contrib"])
    k = r_coord.shape[1]
    assert np.allclose(
        align_to_reference(res.freq.coord.to_numpy()[:, :k], r_coord), r_coord, atol=1e-9, rtol=0
    )
    assert np.allclose(res.freq.cos2.to_numpy()[:, :k], r_cos2, atol=1e-9, rtol=0)
    assert np.allclose(res.freq.contrib.to_numpy()[:, :k], r_contrib, atol=1e-8, rtol=0)


def test_cagalt_quanti_var(r_cagalt_synth_s):
    res = _res()
    r_coord = _dims(r_cagalt_synth_s["quanti.var"]["coord"])
    r_cor = _dims(r_cagalt_synth_s["quanti.var"]["cor"])
    r_cos2 = _dims(r_cagalt_synth_s["quanti.var"]["cos2"])
    k = r_coord.shape[1]
    assert np.allclose(
        align_to_reference(res.quanti_var.coord.to_numpy()[:, :k], r_coord), r_coord, atol=1e-9, rtol=0
    )
    assert np.allclose(
        align_to_reference(res.quanti_var.cor.to_numpy()[:, :k], r_cor), r_cor, atol=1e-9, rtol=0
    )
    assert np.allclose(res.quanti_var.cos2.to_numpy()[:, :k], r_cos2, atol=1e-9, rtol=0)
