"""``predict.*`` — project new individuals onto a fitted model's axes.

Mirrors R FactoMineR's ``predict.PCA`` / ``predict.MCA`` / ``predict.FAMD`` /
``predict.MFA``. Each projects rows that were *not* used to fit the model onto
the model's principal axes, returning their coordinates, squared cosines, and
(where R provides it) the distance to the origin.

Every method reduces to the same final step: build a per-method *scaled* matrix
``M`` of the new individuals (using the **training** centers / scales /
proportions stashed on the result's ``call``), then project it onto the stored
whitened right vectors ``res.svd.V``. :func:`_project_scaled` is that shared
step — the same math the active analyses use for supplementary individuals.

- PCA: ``M = (X - centre) / ecart.type``; ``col.w`` = the active column weights.
- MCA: ``M = (rowprofile - marge.col) / sqrt(marge.col)`` (the CA transition
  formula on the indicator row profile); ``col.w = 1``. Coordinate is the
  *principal* row coordinate (same scale as ``ind$coord``), not the standard
  ``var$coord``.
- FAMD: ``M = [(Q - centre)/sd | (1[cat] - prop)/sqrt(prop)]``; ``col.w = 1``.
- MFA: per-group scaling, then ``col.w`` = the MFA group weights (deferred).

Output column names follow R: PCA/MFA use ``"Dim.1"`` (dot), MCA/FAMD use
``"Dim 1"`` (space).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._result import Block, Result


def _project_scaled(
    M_scaled: np.ndarray,
    col_w: np.ndarray,
    V: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Project rows of a pre-scaled matrix onto the axes defined by ``V``.

    ``M_scaled`` is ``(m × p)``, already centered/scaled per the method's
    convention; ``col_w`` is the length-``p`` active column-weight vector;
    ``V`` is the ``(p × ncp)`` whitened right-singular vectors (``res.svd.V``).
    Returns ``(coord, cos2, dist)`` where ``dist`` is the ``col.w``-weighted
    distance to the origin and ``cos2 = coord² / dist²``.
    """
    sqrt_cw = np.sqrt(col_w)
    coord = (M_scaled * sqrt_cw[None, :]) @ V
    dist2 = (M_scaled**2 * col_w[None, :]).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        cos2 = np.where(dist2[:, None] > 0, coord**2 / dist2[:, None], 0.0)
    return coord, cos2, np.sqrt(dist2)


def _build_indicator(
    newdata: pd.DataFrame,
    fac_cols: list[str],
    training_frame: pd.DataFrame,
) -> np.ndarray:
    """One-hot encode ``newdata[fac_cols]`` using the **training** category sets
    and order (concatenated per variable). Raises on a category not seen in
    training, mirroring R's ``predict`` (which errors on unknown levels)."""
    blocks: list[np.ndarray] = []
    for c in fac_cols:
        train_cats = list(training_frame[c].astype("category").cat.categories)
        s = newdata[c].astype(pd.CategoricalDtype(categories=train_cats))
        codes = s.cat.codes.to_numpy()
        if (codes < 0).any():
            bad = sorted({str(v) for v in newdata[c].to_numpy()[codes < 0]})
            raise ValueError(
                f"predict: column {c!r} has categories not seen in training: {bad}"
            )
        Z = np.zeros((len(s), len(train_cats)), dtype=np.float64)
        Z[np.arange(len(s)), codes] = 1.0
        blocks.append(Z)
    return np.hstack(blocks) if blocks else np.zeros((len(newdata), 0))


def _dim_names(ncp: int, sep: str) -> list[str]:
    return [f"Dim{sep}{i + 1}" for i in range(ncp)]


def predict_pca(res: Result, newdata: pd.DataFrame) -> Block:
    """Project new individuals onto a fitted :func:`factominer.PCA` model."""
    call = res.call
    cols = call["active_col_labels"]
    X_new = newdata[cols].to_numpy(dtype=np.float64)
    mean = np.asarray(call["mean"], dtype=np.float64)
    scale = np.asarray(call["scale"], dtype=np.float64)
    M = (X_new - mean) / scale if call.get("scale_unit", True) else (X_new - mean)
    col_w = np.asarray(call["col_w"], dtype=np.float64)
    coord, cos2, dist = _project_scaled(M, col_w, res.svd.V)
    cols_out = _dim_names(res.svd.V.shape[1], ".")
    idx = list(newdata.index)
    return Block(
        coord=pd.DataFrame(coord, index=idx, columns=cols_out),
        cos2=pd.DataFrame(cos2, index=idx, columns=cols_out),
        dist=pd.Series(dist, index=idx, name="dist"),
    )


def predict_mca(res: Result, newdata: pd.DataFrame) -> Block:
    """Project new individuals onto a fitted :func:`factominer.MCA` model.

    The coordinate is the principal row coordinate (same scale as ``ind$coord``):
    the new individual's indicator row profile, centred on the training column
    margin and projected through the CA transition formula.
    """
    call = res.call
    if call.get("method", "indicator") not in ("indicator", "Indicator"):
        raise NotImplementedError(
            "predict is only supported for MCA(method='indicator'); the Burt "
            "transform reshapes the eigenstructure."
        )
    active = call["active_frame"]
    fac_cols = list(active.columns)
    q = len(fac_cols)
    marge_col = np.asarray(call["marge_col"], dtype=np.float64)
    Z_new = _build_indicator(newdata, fac_cols, active)
    prof = Z_new / q  # each indicator row has q ones -> profile sums to 1
    M = (prof - marge_col) / np.sqrt(marge_col)
    coord, cos2, dist = _project_scaled(M, np.ones_like(marge_col), res.svd.V)
    cols_out = _dim_names(res.svd.V.shape[1], " ")
    idx = list(newdata.index)
    return Block(
        coord=pd.DataFrame(coord, index=idx, columns=cols_out),
        cos2=pd.DataFrame(cos2, index=idx, columns=cols_out),
        dist=pd.Series(dist, index=idx, name="dist"),
    )


def predict_famd(res: Result, newdata: pd.DataFrame) -> Block:
    """Project new individuals onto a fitted :func:`factominer.FAMD` model."""
    call = res.call
    num_cols = list(call["num_cols"])
    fac_cols = list(call["fac_cols"])
    q_center = np.asarray(call["q_center"], dtype=np.float64)
    q_sd = np.asarray(call["q_sd"], dtype=np.float64)
    prop = np.asarray(call["prop"], dtype=np.float64)
    active = call["active_frame"]

    Qn = newdata[num_cols].to_numpy(dtype=np.float64)
    Qs = (Qn - q_center) / q_sd
    Zn = _build_indicator(newdata, fac_cols, active)
    Zs = (Zn - prop) / np.sqrt(prop)
    M = np.hstack([Qs, Zs])
    col_w = np.ones(M.shape[1])
    coord, cos2, dist = _project_scaled(M, col_w, res.svd.V)
    cols_out = _dim_names(res.svd.V.shape[1], " ")
    idx = list(newdata.index)
    return Block(
        coord=pd.DataFrame(coord, index=idx, columns=cols_out),
        cos2=pd.DataFrame(cos2, index=idx, columns=cols_out),
        # R's predict.FAMD names this element ``dist2`` but stores sqrt(dist2).
        dist=pd.Series(dist, index=idx, name="dist"),
    )


def predict_mfa(res: Result, newdata: pd.DataFrame) -> Block:  # noqa: ARG001
    raise NotImplementedError(
        "predict.MFA is implemented in the next sub-batch (C1b); it needs the "
        "per-group training centers/scales/proportions stashed on the MFA result."
    )


_DISPATCH = {
    "PCA": predict_pca,
    "MCA": predict_mca,
    "FAMD": predict_famd,
    "MFA": predict_mfa,
}


def predict(res: Result, newdata: pd.DataFrame) -> Block:
    """Project new individuals onto a fitted model (dispatches on ``res.method``).

    Mirrors R's ``predict`` S3 generic for FactoMineR results. ``newdata`` is a
    DataFrame with the model's active columns (extra columns are ignored;
    categorical columns must use only categories seen during fitting).
    """
    if not isinstance(newdata, pd.DataFrame):
        raise TypeError("newdata must be a pandas DataFrame")
    fn = _DISPATCH.get(res.method)
    if fn is None:
        raise NotImplementedError(f"predict is not supported for method {res.method!r}")
    return fn(res, newdata)
