"""``CaGalt`` — Correspondence Analysis on Generalized Aggregated Lumped Tables.

Ported from R FactoMineR 2.14 ``R/CaGalt.r``. CaGalt relates a frequency /
lexical table ``Y`` (n individuals × p frequency columns) to a set of contextual
covariates ``X`` (n × k). It is a thin orchestrator over :func:`factominer.PCA`:

1. ``P = Y/sum(Y)``; individual masses ``PI = rowSums(P)``, frequency masses
   ``PJ = colSums(P)``.
2. A ``PI``-weighted analysis of the covariates gives the standardized factor
   scores ``phi.stand`` (the ``PI``-orthonormal PC scores of ``X``).
3. Three generalized cross-product tables are built — ``L`` (frequencies ×
   covariate-PCs), ``C`` (the ``PI``-weighted covariate Gram matrix) and ``W``
   (the regression of frequencies on covariates, via ``pinv(C)``).
4. A ``PJ``-weighted PCA of ``cbind(L, W)`` (with ``W`` supplementary) yields the
   eigenvalues, the frequency block, and the covariate block; the individual
   coordinates follow by a transition formula.

Only ``type="s"`` (quantitative, scaled) and ``type="c"`` (quantitative, centred)
are implemented here. ``type="n"`` (qualitative covariates) needs a row-weighted
MCA and is deferred; the bootstrap confidence ellipses (``conf_ellip=True``) are
stochastic and are not implemented.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._result import SVD, Block, Result
from ._scaling import center_scale
from ._svd import standard_svd
from .pca import PCA


def CaGalt(  # noqa: N802 — mirrors R's function name
    Y: pd.DataFrame,
    X: pd.DataFrame,
    type: str = "s",  # noqa: A002 — mirrors R's ``type`` argument
    conf_ellip: bool = False,
    nb_ellip: int = 100,  # noqa: ARG001 — accepted for signature parity (ellipses deferred)
    level_ventil: float = 0.0,
    sx: int | None = None,
    graph: bool = False,  # noqa: ARG001 — accepted for FactoMineR compatibility
    axes: tuple[int, int] = (0, 1),  # noqa: ARG001
) -> Result:
    """Run Correspondence Analysis on Generalized Aggregated Lumped Tables.

    ``Y`` is a frequency table (n × p, non-negative counts); ``X`` is the table
    of contextual covariates (n × k). ``type`` is ``"s"`` (quantitative scaled to
    unit variance, the default) or ``"c"`` (quantitative, centred only).

    Returns a :class:`Result` with ``eig``, ``ind`` (individual coord/cos2),
    ``freq`` (frequency-column coord/cos2/contrib), ``quanti_var`` (covariate
    coord/cor/cos2), and ``svd``.
    """
    if not isinstance(Y, pd.DataFrame) or not isinstance(X, pd.DataFrame):
        raise TypeError("Y and X must be pandas DataFrames")
    if conf_ellip:
        raise NotImplementedError(
            "CaGalt confidence ellipses (conf_ellip=True) are a stochastic "
            "bootstrap and are not implemented."
        )
    if type == "n":
        raise NotImplementedError(
            "CaGalt with qualitative covariates (type='n') needs a row-weighted "
            "MCA; it is deferred to a follow-up batch. Use type='s' or 'c'."
        )
    if type not in ("s", "c"):
        raise ValueError(f"type must be 's', 'c', or 'n'; got {type!r}")
    if level_ventil and level_ventil > 0:
        raise NotImplementedError("CaGalt ventilation (level_ventil>0) is deferred.")

    Yarr = Y.to_numpy(dtype=np.float64)
    Xarr = X.to_numpy(dtype=np.float64)
    n, p = Yarr.shape
    k = Xarr.shape[1]

    P = Yarr / Yarr.sum()
    pi_ = P.sum(axis=1)  # individual masses (n,)
    pj = P.sum(axis=0)   # frequency masses (p,)

    # --- covariate analysis: PI-orthonormal standardized PC scores ----------
    ncp = min(n - 1, k) if sx is None else int(min(sx, n - 1, k))
    Xc, _, _ = center_scale(Xarr, scale_unit=(type == "s"), row_w=pi_)
    sqrt_pi = np.sqrt(pi_)
    # R's svd.triplet: svd$U = (left vectors of the PI-weighted X) / sqrt(PI),
    # i.e. the PI-orthonormal scores. Compute them directly so we don't depend
    # on the inner PCA's whitening convention.
    u_w, _, _ = standard_svd(sqrt_pi[:, None] * Xc, ncp)
    phi_stand = u_w / sqrt_pi[:, None]  # n × ncp

    # --- generalized cross-product tables -----------------------------------
    # L: frequencies × covariate-PCs (row-divided by the frequency masses).
    L = (P.T @ phi_stand) / pj[:, None]            # p × ncp
    T = P.T @ Xc                                   # p × k
    Csqp = Xc * sqrt_pi[:, None]
    Cmat = Csqp.T @ Csqp                           # k × k  (= Xc' diag(PI) Xc)
    W = (T @ np.linalg.pinv(Cmat)) / pj[:, None]   # p × k  (ginv = pinv)

    # --- inner PJ-weighted PCA of cbind(L, W), W supplementary --------------
    pc_labels = [f"PC{d + 1}" for d in range(ncp)]
    var_labels = list(X.columns)
    inner_frame = pd.DataFrame(
        np.hstack([L, W]), index=list(Y.columns), columns=pc_labels + var_labels
    )
    inner = PCA(
        inner_frame,
        scale_unit=False,
        ncp=ncp,
        row_w=pj,
        quanti_sup=list(range(ncp, ncp + k)),
    )
    n_pc = inner.ind.coord.shape[1]
    dim_names = [f"Dim.{d + 1}" for d in range(n_pc)]

    # --- individual coordinates via the transition formula ------------------
    # R: coord.ind = sweep(P %*% diag.L$svd$U, 1, PI, "/"); diag.L$svd$U is the
    # *un-whitened* left vectors = inner.svd.U / sqrt(PJ).
    u_inner = inner.svd.U[:, :n_pc] / np.sqrt(pj)[:, None]
    coord_ind = (P @ u_inner) / pi_[:, None]       # n × n_pc
    ss = (coord_ind**2).sum(axis=1, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        cos2_ind = np.where(ss > 0, coord_ind**2 / ss, 0.0)

    ind_block = Block(
        coord=pd.DataFrame(coord_ind, index=list(Y.index), columns=dim_names),
        cos2=pd.DataFrame(cos2_ind, index=list(Y.index), columns=dim_names),
    )
    freq_block = Block(
        coord=inner.ind.coord,
        cos2=inner.ind.cos2,
        contrib=inner.ind.contrib,
    )
    # quanti.var = the inner PCA's supplementary-variable block (coord/cor/cos2).
    quanti_var = Block(
        coord=inner.quanti_sup.coord,
        cor=inner.quanti_sup.cor,
        cos2=inner.quanti_sup.cos2,
    )

    return Result(
        eig=inner.eig,
        svd=SVD(vs=inner.svd.vs.copy(), U=inner.svd.U.copy(), V=inner.svd.V.copy()),
        call={
            "type": type,
            "ncp": ncp,
            "row_masses": pi_.copy(),
            "col_masses": pj.copy(),
            "Y_columns": list(Y.columns),
            "X_columns": var_labels,
        },
        ind=ind_block,
        freq=freq_block,
        quanti_var=quanti_var,
        method="CaGalt",
    )
