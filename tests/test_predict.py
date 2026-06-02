"""Parity tests for ``predict.*`` — project held-out individuals onto a model.

Each R fixture fits on a row slice and predicts the complementary held-out
rows; the Python side reproduces the identical split with the bundled loaders.
``coord`` is sign-dependent (the model's axis signs) so it is sign-aligned per
axis before comparison; ``cos2`` / ``dist`` are sign-invariant. Projected
quantities are held to the supplementary tier (1e-7). Fixtures are positional
(jsonlite drops row names), so individuals align in newdata order.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from factominer import FAMD, MCA, PCA, predict
from factominer._sign import align_to_reference
from factominer.datasets import load_decathlon, load_poison, load_tea


def _mat(records: list[dict]) -> np.ndarray:
    """Build an ``(n × k)`` array from a jsonlite list-of-records, keeping only
    the ``Dim.k`` / ``Dim k`` columns (jsonlite also emits a ``_row`` name
    column) and ordering them by their trailing index."""
    df = pd.DataFrame(records)
    dim_cols = [c for c in df.columns if str(c).startswith("Dim")]
    dim_cols = sorted(dim_cols, key=lambda c: int(str(c).replace("Dim.", "").replace("Dim ", "").strip()))
    return df[dim_cols].to_numpy(dtype=np.float64)


def test_predict_pca(r_predict_pca_decathlon):
    deca = load_decathlon().iloc[:, :10]
    res = PCA(deca.iloc[:38], scale_unit=True, ncp=5)
    p = predict(res, deca.iloc[38:41])

    r_coord = _mat(r_predict_pca_decathlon["coord"])
    r_cos2 = _mat(r_predict_pca_decathlon["cos2"])
    r_dist = np.asarray(r_predict_pca_decathlon["dist"], dtype=np.float64)

    assert np.allclose(align_to_reference(p.coord.to_numpy(), r_coord), r_coord, atol=1e-7, rtol=0)
    assert np.allclose(p.cos2.to_numpy(), r_cos2, atol=1e-7, rtol=0)
    assert np.allclose(p.dist.to_numpy(), r_dist, atol=1e-7, rtol=0)


def test_predict_mca(r_predict_mca_tea):
    tea = load_tea().iloc[:, :18]
    res = MCA(tea.iloc[5:300], ncp=5)
    p = predict(res, tea.iloc[0:5])

    r_coord = _mat(r_predict_mca_tea["coord"])
    r_cos2 = _mat(r_predict_mca_tea["cos2"])
    k = r_coord.shape[1]

    assert np.allclose(
        align_to_reference(p.coord.to_numpy()[:, :k], r_coord), r_coord, atol=1e-7, rtol=0
    )
    assert np.allclose(p.cos2.to_numpy()[:, :k], r_cos2, atol=1e-7, rtol=0)
    # R's predict.MCA returns no `dist` element.
    assert "dist" not in r_predict_mca_tea


def test_predict_famd(r_predict_famd_poison):
    poison = load_poison()
    res = FAMD(poison.iloc[5:55], ncp=5)
    p = predict(res, poison.iloc[0:5])

    r_coord = _mat(r_predict_famd_poison["coord"])
    r_cos2 = _mat(r_predict_famd_poison["cos2"])
    # R's predict.FAMD names this `dist2` but stores sqrt(dist2).
    r_dist = np.asarray(r_predict_famd_poison["dist2"], dtype=np.float64)
    k = r_coord.shape[1]

    assert np.allclose(
        align_to_reference(p.coord.to_numpy()[:, :k], r_coord), r_coord, atol=1e-7, rtol=0
    )
    assert np.allclose(p.cos2.to_numpy()[:, :k], r_cos2, atol=1e-7, rtol=0)
    assert np.allclose(p.dist.to_numpy(), r_dist, atol=1e-7, rtol=0)


def test_predict_mfa(r_predict_mfa_poison):
    from factominer import MFA

    poison = load_poison()
    res = MFA(
        poison.iloc[5:55],
        group=[2, 2, 5, 6],
        type=["s", "n", "n", "n"],
        name_group=["desc", "desc2", "symptom", "eat"],
    )
    p = predict(res, poison.iloc[0:5])

    r_coord = _mat(r_predict_mfa_poison["coord"])
    r_cos2 = _mat(r_predict_mfa_poison["cos2"])
    r_dist = np.asarray(r_predict_mfa_poison["dist"], dtype=np.float64)
    k = r_coord.shape[1]

    assert np.allclose(
        align_to_reference(p.coord.to_numpy()[:, :k], r_coord), r_coord, atol=1e-7, rtol=0
    )
    assert np.allclose(p.cos2.to_numpy()[:, :k], r_cos2, atol=1e-7, rtol=0)
    assert np.allclose(p.dist.to_numpy(), r_dist, atol=1e-7, rtol=0)
