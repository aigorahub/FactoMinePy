"""Generalized Procrustes Analysis — FactoMineR-compatible (deterministic core).

Ported from R FactoMineR 2.14 ``R/GPA.R`` for the common case: K configurations
of the same N objects, no missing values, equal configuration widths, and
``scale=True``.

Important parity note: **R's GPA is stochastic.** ``GPA()`` runs 5 random
restarts (``f1ter``, unseeded ``sample()`` + random sign/column flips) and keeps
the best, and ``procrustesbis`` uses ``rnorm`` to complete a rank-deficient
basis. This port implements the **deterministic single-start core**
(``algogpa``) and skips the random multi-start. For a well-conditioned,
full-rank dataset the single start converges to the same optimum R finds, up to
a global rotation/reflection — which is the inherent gauge freedom of Procrustes
analysis. Consequently:

- ``RV``, ``RVs``, ``simi`` are computed from the **raw** configurations and are
  rotation/scale-invariant, so they match R **exactly**.
- ``consensus`` and ``Xfin`` match R only **up to a global orthogonal
  transform**; compare them via rotation-invariant quantities (inter-point
  distances) or after a Procrustes alignment.

For the no-missing, equal-width, uniform-weight case the general GPA reduces
cleanly: the per-configuration centering operator is the same idempotent
projection ``C = I − (1/N)11ᵀ`` for every configuration, so the consensus
metric ``invgC = C/K``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class GPAResult:
    """FactoMineR ``GPA``-shaped result.

    - ``consensus``: the N×D consensus configuration (rotated to principal axes).
    - ``Xfin``: list of K N×D arrays, each input configuration after full
      Procrustes alignment (translation + rotation + scaling) into the
      consensus space.
    - ``RV`` / ``RVs`` / ``simi``: K×K DataFrames of inter-configuration
      agreement (Escoufier RV, standardized RV, Procrustes similarity).
    - ``scaling``: length-K isotropic scaling weights (``poids``).
    - ``correlations``: per-configuration correlation of the original variables
      with the consensus axes.
    """

    consensus: pd.DataFrame
    Xfin: list[pd.DataFrame]
    RV: pd.DataFrame
    RVs: pd.DataFrame
    simi: pd.DataFrame
    scaling: pd.Series
    correlations: dict[str, pd.DataFrame] = field(default_factory=dict)
    call: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"<factominer.GPA groups={self.RV.shape[0]} consensus_dims={self.consensus.shape[1]}>"


def GPA(  # noqa: N802 — mirrors R's function name
    df: pd.DataFrame,
    group: list[int],
    scale: bool = True,
    tolerance: float = 1e-10,
    nbiteration: int = 200,
    name_group: list[str] | None = None,
    graph: bool = False,  # noqa: ARG001 — accepted for FactoMineR compatibility
) -> GPAResult:
    """Generalized Procrustes Analysis.

    Parameters
    ----------
    df : DataFrame (N objects × sum(group) columns)
        Horizontal concatenation of the K configurations.
    group : list[int]
        Column count of each configuration (must currently be equal-width).
    scale : bool
        Whether to estimate per-configuration isotropic scaling weights.
    tolerance, nbiteration : float, int
        Convergence controls for the iterative consensus.
    name_group : list[str] | None
        Names for the K configurations (default ``group.1`` ...).
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    X = df.to_numpy(dtype=np.float64)
    if np.isnan(X).any():
        raise NotImplementedError("GPA with missing values is not yet supported")
    n = X.shape[0]
    K = len(group)
    if len(set(group)) != 1:
        raise NotImplementedError("GPA currently requires equal-width configurations")
    p = group[0]
    if name_group is None:
        name_group = [f"group.{i + 1}" for i in range(K)]

    # Split into K raw configurations (used as-is for RV / simi).
    raw = []
    off = 0
    for g in group:
        raw.append(X[:, off:off + g].copy())
        off += g

    # calibre: per-configuration PCA pre-rotation (center + rotate to principal
    # axes; scale.unit=FALSE → centering only, no standardization).
    calib = [_calibre(Xk) for Xk in raw]

    # Centering projector C = I − (1/N) 11ᵀ (idempotent). All configs share it.
    C = np.eye(n) - np.ones((n, n)) / n

    # Global normalization so the grand weighted SS = K (one common scalar).
    lambda2 = sum(np.trace(Ck.T @ C @ Ck) for Ck in calib)
    lam = np.sqrt(K / lambda2)
    Xn = [Ck * lam for Ck in calib]

    # W12 = diag(1/sqrt(per-config Procrustes norm)).
    norms = np.array([np.trace(Xk.T @ C @ Xk) for Xk in Xn])
    W12 = np.diag(1.0 / np.sqrt(norms))

    invgC = C / K  # ginv(Cc) with Cc = K·C and C idempotent

    R = [np.eye(p) for _ in range(K)]
    pds = np.ones(K)

    def consensus_accumulator():
        return sum(pds[i] * (C @ Xn[i] @ R[i]) for i in range(K))

    def loss():
        s = consensus_accumulator()
        return K - np.trace(s.T @ invgC @ s)

    prev = loss()
    for _ in range(nbiteration):
        # Rotation sub-step (sequential / Gauss–Seidel): rotate each config
        # toward the leave-one-out consensus.
        for k in range(K):
            others = sum(pds[i] * (C @ Xn[i] @ R[i]) for i in range(K) if i != k)
            target = invgC @ others
            R[k] = _procrustes_H(C @ Xn[k], target)
        if scale:
            B = [C @ Xn[k] @ R[k] for k in range(K)]
            matY = np.array([[np.trace(B[a].T @ invgC @ B[b]) for b in range(K)] for a in range(K)])
            M = W12 @ matY @ W12
            vals, vecs = np.linalg.eigh(M)
            vec = vecs[:, int(np.argmax(vals))]
            if np.sum(vec < 0) == len(vec):
                vec = -vec
            pds = np.sqrt(K) * (W12 @ vec)
        cur = loss()
        if abs(prev - cur) < tolerance:
            prev = cur
            break
        prev = cur

    # Consensus + final eigen-rotation to principal axes.
    s = consensus_accumulator()
    pp = invgC @ s
    ppvals, ppvecs = np.linalg.eigh(pp.T @ (K * C) @ pp)
    order = np.argsort(ppvals)[::-1]
    ppvecs = ppvecs[:, order]
    consensus = pp @ ppvecs

    Xfin = [pds[k] * (C @ Xn[k] @ R[k]) @ ppvecs for k in range(K)]

    # Trim trailing near-zero consensus dimensions (R's `fina`).
    colmax = np.abs(consensus).max(axis=0)
    keep = colmax > np.sqrt(np.finfo(float).eps)
    fina = int(np.max(np.where(keep)[0]) + 1) if keep.any() else consensus.shape[1]
    consensus = consensus[:, :fina]
    Xfin = [xf[:, :fina] for xf in Xfin]

    # RV / RVs / simi on the RAW configurations.
    RV = np.eye(K)
    RVs = np.eye(K)
    sim = np.eye(K)
    for i in range(K):
        for j in range(i + 1, K):
            rv, rvs = _coeff_rv(raw[i], raw[j])
            RV[i, j] = RV[j, i] = rv
            RVs[i, j] = RVs[j, i] = rvs
            sij = _similarite(raw[i], raw[j])
            sim[i, j] = sim[j, i] = sij

    # Per-configuration correlations of original variables with the consensus.
    correlations: dict[str, pd.DataFrame] = {}
    for i in range(K):
        Xc = raw[i] - raw[i].mean(axis=0)
        cor = np.zeros((p, fina))
        for a in range(p):
            for b in range(fina):
                cor[a, b] = _safe_corr(Xc[:, a], consensus[:, b])
        correlations[name_group[i]] = pd.DataFrame(
            cor, index=[f"{name_group[i]}.v{a + 1}" for a in range(p)],
            columns=[f"Dim.{b + 1}" for b in range(fina)],
        )

    idx = list(df.index)
    dim_cols = [f"Dim.{b + 1}" for b in range(fina)]
    return GPAResult(
        consensus=pd.DataFrame(consensus, index=idx, columns=dim_cols),
        Xfin=[pd.DataFrame(xf, index=idx, columns=dim_cols) for xf in Xfin],
        RV=pd.DataFrame(RV, index=name_group, columns=name_group),
        RVs=pd.DataFrame(RVs, index=name_group, columns=name_group),
        simi=pd.DataFrame(sim, index=name_group, columns=name_group),
        scaling=pd.Series(pds, index=name_group, name="scaling"),
        correlations=correlations,
        call={"group": list(group), "scale": scale, "name_group": list(name_group)},
    )


def _calibre(Xk: np.ndarray) -> np.ndarray:
    """Per-configuration PCA pre-rotation: center columns, rotate to principal
    axes (scale.unit=FALSE). For a full-rank config this is an orthogonal
    rotation of the centered data; the result has the same shape."""
    Xc = Xk - Xk.mean(axis=0)
    _, _, vt = np.linalg.svd(Xc, full_matrices=False)
    return Xc @ vt.T


def _procrustes_H(X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
    """Orthogonal Procrustes rotation H (reflections allowed) mapping centered
    X1 toward X2: H = U Vᵀ from the SVD of X1cᵀ X2c. Applied as X1 @ H."""
    X1c = X1 - X1.mean(axis=0)
    X2c = X2 - X2.mean(axis=0)
    A = X1c.T @ X2c
    U, _, Vt = np.linalg.svd(A)
    return U @ Vt


def _coeff_rv(X: np.ndarray, Y: np.ndarray) -> tuple[float, float]:
    """FactoMineR coeffRV: Escoufier RV and the standardized (diagonal-removed)
    RVstd between two centered configurations."""
    Xc = X - X.mean(axis=0)
    Yc = Y - Y.mean(axis=0)
    W1 = Xc @ Xc.T
    W2 = Yc @ Yc.T
    rv = np.trace(W1 @ W2) / np.sqrt(np.trace(W1 @ W1) * np.trace(W2 @ W2))
    W1t = W1 - np.diag(np.diag(W1))
    W2t = W2 - np.diag(np.diag(W2))
    rvs = np.trace(W1t @ W2t) / np.sqrt(np.trace(W1t @ W1t) * np.trace(W2t @ W2t))
    return float(rv), float(rvs)


def _similarite(X: np.ndarray, Y: np.ndarray) -> float:
    """Procrustes congruence: rotate Y onto X, then trace(Xᵀ y)/sqrt(tr(XᵀX) tr(yᵀy))."""
    Xc = X - X.mean(axis=0)
    Yc = Y - Y.mean(axis=0)
    y = Yc @ _procrustes_H(Yc, Xc)
    return float(np.trace(Xc.T @ y) / np.sqrt(np.trace(Xc.T @ Xc) * np.trace(y.T @ y)))


def _safe_corr(a: np.ndarray, b: np.ndarray) -> float:
    sa, sb = a.std(), b.std()
    if sa == 0 or sb == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])
