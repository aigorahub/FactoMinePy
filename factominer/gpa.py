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
    panova: dict[str, pd.DataFrame] = field(default_factory=dict)
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
    p = max(group)  # common working width; narrower configs are zero-padded
    if name_group is None:
        name_group = [f"group.{i + 1}" for i in range(K)]

    # Split into K raw configurations (used as-is for RV / simi).
    raw = []
    off = 0
    for g in group:
        raw.append(X[:, off:off + g].copy())
        off += g

    # calibre: per-configuration PCA pre-rotation (center + rotate to principal
    # axes; scale.unit=FALSE → centering only, no standardization). Narrower
    # configurations are zero-padded to the common width max(group), mirroring
    # R, which repads each calibrated config to nbcolonne = max rank (GPA.R's
    # `calibre`). With no missing values every per-config metric is the same
    # idempotent C, so `invgC = C/K` stays exact for unequal widths too.
    calib = []
    for Xk in raw:
        Ck = _calibre(Xk)
        if Ck.shape[1] < p:
            Ck = np.hstack([Ck, np.zeros((n, p - Ck.shape[1]))])
        calib.append(Ck)

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

    # RV / RVs / simi on the RAW configurations. R fills the diagonal too
    # (loop j in i:K): RV[i,i]=1 and simi[i,i]=1, but RVs[i,i] is the
    # standardized self-RV (coeffRV(Xi,Xi)$rvstd), not 1.
    RV = np.zeros((K, K))
    RVs = np.zeros((K, K))
    sim = np.zeros((K, K))
    for i in range(K):
        for j in range(i, K):
            rv, rvs = _coeff_rv(raw[i], raw[j])
            RV[i, j] = RV[j, i] = rv
            RVs[i, j] = RVs[j, i] = rvs
            sij = _similarite(raw[i], raw[j])
            sim[i, j] = sim[j, i] = sij

    # Per-configuration correlations of the original (centered) variables with
    # the consensus axes — `cor(scale(config_i, scale=FALSE), consensus)` per R
    # (GPA.R L816-821). Each config contributes its own `group[i]` variables.
    df_cols = list(df.columns)
    dim_cols = [f"Dim.{b + 1}" for b in range(fina)]
    correlations: dict[str, pd.DataFrame] = {}
    col_off = 0
    cor_mats: list[np.ndarray] = []
    for i in range(K):
        gi = group[i]
        cfg_cols = df_cols[col_off : col_off + gi]
        col_off += gi
        Xc = raw[i] - raw[i].mean(axis=0)
        cor = np.zeros((gi, fina))
        for a in range(gi):
            for b in range(fina):
                cor[a, b] = _safe_corr(Xc[:, a], consensus[:, b])
        cor_mats.append(cor)
        correlations[f"cor {name_group[i]}"] = pd.DataFrame(
            cor, index=[str(c) for c in cfg_cols], columns=dim_cols
        )
    # R appends an elementwise-mean "averagecor" only when all configs are the
    # same width (GPA.R L824-836).
    if len(set(group)) == 1:
        correlations["averagecor"] = pd.DataFrame(
            np.mean(cor_mats, axis=0),
            index=[f"V{a + 1}" for a in range(group[0])],
            columns=dim_cols,
        )

    # --- PANOVA (Procrustes ANOVA, the no-missing "sansvm" branch, GPA.R
    #     L110-230): per-object / per-config / per-dimension sum-of-squares
    #     tables as percent of total SS. The SStotal columns and the summary
    #     rows are rotation/reflection-invariant (Tier-1 exact); the per-axis
    #     splits are gauge-dependent (Tier-2). ---
    cons = consensus
    xfin_arr = np.stack(Xfin, axis=2)  # (n × fina × K)
    ss_fit_obj = K * (cons**2).sum(axis=1)
    ss_res_obj = ((xfin_arr - cons[:, :, None]) ** 2).sum(axis=(1, 2))
    ss_tot_obj = (xfin_arr**2).sum(axis=(1, 2))
    panova_objet = _panova_table(
        ss_fit_obj, ss_res_obj, ss_tot_obj, list(df.index), ("SSfit", "SSresidual", "SStotal"), K
    )
    ss_fit_cfg = np.zeros(K)  # R hardcodes SSfit = 0 in the sansvm config table
    ss_res_cfg = ((xfin_arr - cons[:, :, None]) ** 2).sum(axis=(0, 1))
    ss_tot_cfg = (xfin_arr**2).sum(axis=(0, 1))
    panova_config = _panova_table(
        ss_fit_cfg, ss_res_cfg, ss_tot_cfg, list(name_group), ("SSfit", "SSresidual", "SStotal"), K
    )
    ss_cons_dim = K * (cons**2).sum(axis=0)
    ss_res_dim = ((xfin_arr - cons[:, :, None]) ** 2).sum(axis=(0, 2))
    ss_tot_dim = (xfin_arr**2).sum(axis=(0, 2))
    panova_dim = _panova_table(
        ss_cons_dim, ss_res_dim, ss_tot_dim, dim_cols, ("Consensus", "residus", "Total"), K
    )
    panova = {"objet": panova_objet, "config": panova_config, "dimension": panova_dim}

    idx = list(df.index)
    return GPAResult(
        consensus=pd.DataFrame(consensus, index=idx, columns=dim_cols),
        Xfin=[pd.DataFrame(xf, index=idx, columns=dim_cols) for xf in Xfin],
        RV=pd.DataFrame(RV, index=name_group, columns=name_group),
        RVs=pd.DataFrame(RVs, index=name_group, columns=name_group),
        simi=pd.DataFrame(sim, index=name_group, columns=name_group),
        scaling=pd.Series(pds, index=name_group, name="scaling"),
        correlations=correlations,
        panova=panova,
        call={"group": list(group), "scale": scale, "name_group": list(name_group)},
    )


def _panova_table(
    c0: np.ndarray,
    c1: np.ndarray,
    c2: np.ndarray,
    row_labels: list[str],
    col_labels: tuple[str, str, str],
    nbj: int,
) -> pd.DataFrame:
    """One PANOVA sub-table: stack the three sum-of-squares columns, append a
    column-sum summary row, then express as percent of total SS (÷ nbj · 100)."""
    mat = np.column_stack([np.asarray(c0), np.asarray(c1), np.asarray(c2)])
    mat = np.vstack([mat, mat.sum(axis=0)])
    mat = mat / nbj * 100.0
    return pd.DataFrame(mat, index=[*row_labels, "sum"], columns=list(col_labels))


def _calibre(Xk: np.ndarray) -> np.ndarray:
    """Per-configuration PCA pre-rotation: center columns, rotate to principal
    axes (scale.unit=FALSE). For a full-rank config this is an orthogonal
    rotation of the centered data; the result has the same shape."""
    Xc = Xk - Xk.mean(axis=0)
    _, _, vt = np.linalg.svd(Xc, full_matrices=False)
    return Xc @ vt.T


def _procrustes_H(X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
    """(Semi-)orthogonal Procrustes mapping H of centered X1 toward X2 from the
    SVD of ``X1cᵀ X2c = U Σ Vᵀ``: ``H = U[:, :k] Vᵀ`` with ``k = min(p1, p2)``,
    applied as ``X1 @ H``. For equal widths this is the square ``U Vᵀ`` rotation;
    for configurations of different widths (GPA `similarite` on raw configs) it
    is the ``p1 × p2`` semi-orthogonal map."""
    X1c = X1 - X1.mean(axis=0)
    X2c = X2 - X2.mean(axis=0)
    A = X1c.T @ X2c
    U, _, Vt = np.linalg.svd(A)
    k = min(U.shape[1], Vt.shape[0])
    return U[:, :k] @ Vt[:k, :]


def _coeff_rv(X: np.ndarray, Y: np.ndarray) -> tuple[float, float]:
    """FactoMineR ``coeffRV``: Escoufier RV and the standardized RVstd.

    RVstd is the Kazi-Aoual / Josse moment standardization
    ``(rv − E[rv]) / sqrt(Var[rv])`` under the row-permutation null, using the
    analytic moment formulas (FactoMineR's ``n >= 6`` branch). Requires n >= 6
    (smaller n uses exact permutation enumeration, not yet ported)."""
    Xc = X - X.mean(axis=0)
    Yc = Y - Y.mean(axis=0)
    W1 = Xc @ Xc.T
    W2 = Yc @ Yc.T
    rv = np.trace(W1 @ W2) / np.sqrt(np.trace(W1 @ W1) * np.trace(W2 @ W2))

    n = X.shape[0]
    if n < 6:
        raise NotImplementedError("coeffRV RVstd needs n >= 6 (permutation path not ported)")
    tt, te = np.trace(W1), np.trace(W2)
    t2, t2e = np.trace(W1 @ W1), np.trace(W2 @ W2)
    s2, s2e = float(np.sum(np.diag(W1) ** 2)), float(np.sum(np.diag(W2) ** 2))
    betax, betay = tt**2 / t2, te**2 / t2e
    alphax, alphay = n - 1 - betax, n - 1 - betay
    deltax, deltay = s2 / t2, s2e / t2e
    gammax = (n - 1) * (n * (n + 1) * deltax - (n - 1) * (betax + 2)) / ((n - 3) * (n - 1 - betax))
    gammay = (n - 1) * (n * (n + 1) * deltay - (n - 1) * (betay + 2)) / ((n - 3) * (n - 1 - betay))
    esperance = np.sqrt(betax) * np.sqrt(betay) / (n - 1)
    variance = (
        2 * alphay * alphax / ((n + 1) * (n - 1) ** 2 * (n - 2))
        * (1 + (n - 3) * gammax * gammay / (2 * n * (n - 1)))
    )
    rvs = (rv - esperance) / np.sqrt(variance)
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
