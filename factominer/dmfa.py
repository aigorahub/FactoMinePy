"""Dual Multiple Factor Analysis — FactoMineR-compatible.

Ported from R FactoMineR 2.14 ``R/DMFA.R``. DMFA is the *dual* of MFA: the same
variables are measured on individuals split into groups by a factor, and the
object of study is how the cloud / covariance structure of the variables varies
across the levels of that grouping factor.

Algorithm (``DMFA.R`` line refs):

1. Reorder columns to ``[factor, quali.sup, active, quanti.sup]`` (L13); the
   grouping factor becomes column 0.
2. For each group level, center (and scale, if ``scale_unit``) the sub-table by
   that group's *own* mean/sd (R's ``scale()``, L32) and form its covariance
   (``scale_unit=False``) or correlation (``scale_unit=True``) matrix ``Cov[j]``
   (L33-34). This per-group standardization — not MFA's ``1/λ₁`` weighting — is
   DMFA's normalization.
3. Stack the per-group-centered sub-tables and prepend the factor (L36-40), then
   run a plain (unweighted) ``PCA`` with the factor as ``quali.sup`` and any
   supplementary quantitatives carried through (L41). The inner PCA's own
   ``scale_unit`` stays ``True`` (it re-standardizes globally) — decoupled from
   DMFA's per-group ``scale_unit``.
4. Reorder ``ind`` back to the original row order (L49-52).
5. DMFA group block (L65-82): ``group.coord[j,s] = v_sᵀ Cov_active_j v_s / λ_s``
   where ``v_s`` is the global variable *loading* (``res.pca$var$coord[:,s]``)
   and ``λ_s`` the global eigenvalue; ``group.coord_n[j,s] =
   coord / λ₁(Cov_active_j)``; ``group.cos2[j,s] = coord² / Σλ(Cov_active_j)² ·
   100``. Plus ``var.partiel[j] = cor(Xc_j, FS_j)`` and ``cor.dim.gr[j] =
   cor(FS_j)`` (L61-62).

Supplementary qualitatives (``quali_sup``) and the interaction-factor branch
(L42-47) are not yet implemented; pass only ``num_fact`` and optional
``quanti_sup``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from ._result import SVD, Block
from ._scaling import column_indices
from .pca import PCA


@dataclass(frozen=True)
class DMFAResult:
    """FactoMineR ``DMFA``-shaped result.

    ``group_coord`` / ``group_coord_n`` / ``group_cos2`` are ``ng × ncp`` (one
    row per group level). ``var_partiel`` / ``cor_dim_gr`` / ``Cov`` / ``Xc`` are
    dicts keyed by group level.
    """

    eig: pd.DataFrame
    svd: SVD
    ind: Block
    var: Block
    group_coord: pd.DataFrame
    group_coord_n: pd.DataFrame
    group_cos2: pd.DataFrame
    var_partiel: dict[str, pd.DataFrame]
    cor_dim_gr: dict[str, pd.DataFrame]
    Cov: dict[str, pd.DataFrame]
    Xc: dict[str, pd.DataFrame]
    quanti_sup: Block | None = None
    call: dict[str, Any] = field(default_factory=dict)
    method: str = "DMFA"

    def __repr__(self) -> str:
        return f"<factominer.DMFA groups={self.group_coord.shape[0]} ncp={self.eig.shape[0]}>"


def _scale(block: np.ndarray, scale_unit: bool) -> np.ndarray:
    """R ``scale()``: center by column mean, optionally divide by sample (n−1) sd."""
    centered = block - block.mean(axis=0)
    if scale_unit:
        sd = block.std(axis=0, ddof=1)
        sd = np.where(sd == 0, 1.0, sd)
        return centered / sd
    return centered


def _corr_cols(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Column-wise Pearson correlation matrix between the columns of ``a`` and
    ``b`` (unweighted, R's ``cor(a, b)``)."""
    ac = a - a.mean(axis=0)
    bc = b - b.mean(axis=0)
    sa = np.sqrt((ac**2).sum(axis=0))
    sb = np.sqrt((bc**2).sum(axis=0))
    out = (ac.T @ bc) / np.outer(sa, sb)
    return out


def DMFA(  # noqa: N802 — mirrors R's function name
    don: pd.DataFrame,
    num_fact: int | str | None = None,
    scale_unit: bool = True,
    ncp: int = 5,
    quanti_sup: list[int] | list[str] | None = None,
    quali_sup: list[int] | list[str] | None = None,
    graph: bool = False,  # noqa: ARG001 — accepted for FactoMineR compatibility
) -> DMFAResult:
    """Run Dual Multiple Factor Analysis.

    ``num_fact`` is the grouping factor column (name or 0-indexed position;
    defaults to the last column). ``quanti_sup`` lists supplementary
    quantitative columns. Returns a :class:`DMFAResult`.
    """
    if not isinstance(don, pd.DataFrame):
        raise TypeError("don must be a pandas DataFrame")
    if quali_sup is not None:
        raise NotImplementedError(
            "DMFA supplementary qualitative variables (quali_sup) are not yet implemented."
        )

    n_total_cols = don.shape[1]
    fact_pos = (n_total_cols - 1) if num_fact is None else column_indices(don.columns, [num_fact])[0]
    quanti_pos = column_indices(don.columns, quanti_sup)
    drop = {fact_pos, *quanti_pos}
    other_pos = [i for i in range(n_total_cols) if i not in drop]
    # R/DMFA.R:13 — [factor, quali.sup(none), active, quanti.sup].
    new_order = [fact_pos] + other_pos + quanti_pos
    don2 = don.iloc[:, new_order].copy()

    factor = don2.iloc[:, 0].astype("category")
    levels = list(factor.cat.categories)
    # R prefixes purely-numeric level names with "Gr" (L18).
    if all(str(lv).isdigit() for lv in levels):
        levels = [f"Gr{lv}" for lv in levels]
        factor = factor.cat.rename_categories(levels)
    ng = len(levels)

    n_active = len(other_pos)
    n_quanti = len(quanti_pos)
    # Columns of Xc (active then quanti.sup) and of the stacked X (factor first).
    xc_labels = list(don2.columns[1 : 1 + n_active + n_quanti])

    # Per-group centered/scaled sub-tables, covariances, and the stacked matrix.
    block_vals = don2.iloc[:, 1 : 1 + n_active + n_quanti].to_numpy(dtype=np.float64)
    fac_codes = factor.to_numpy()
    Xc: dict[str, pd.DataFrame] = {}
    Cov: dict[str, pd.DataFrame] = {}
    stacked_parts: list[pd.DataFrame] = []
    for lv in levels:
        mask = fac_codes == lv
        sub = _scale(block_vals[mask], scale_unit)
        idx = don2.index[mask]
        xc_df = pd.DataFrame(sub, index=idx, columns=xc_labels)
        Xc[lv] = xc_df
        cov = np.corrcoef(sub, rowvar=False) if scale_unit else np.cov(sub, rowvar=False, ddof=1)
        Cov[lv] = pd.DataFrame(cov, index=xc_labels, columns=xc_labels)
        stacked_parts.append(xc_df)

    x_stacked = pd.concat(stacked_parts, axis=0)
    x_stacked.insert(0, str(don2.columns[0]), factor.loc[x_stacked.index].astype(object).to_numpy())

    quanti_sup_in_x = list(range(1 + n_active, 1 + n_active + n_quanti)) if n_quanti else None
    res_pca = PCA(x_stacked, scale_unit=True, ncp=ncp, quali_sup=[0], quanti_sup=quanti_sup_in_x)

    # Reorder ind back to the original row order (R/DMFA.R:49-52).
    orig_index = list(don2.index)
    ind_block = Block(
        coord=res_pca.ind.coord.loc[orig_index].copy(),
        cos2=res_pca.ind.cos2.loc[orig_index].copy(),
        contrib=res_pca.ind.contrib.loc[orig_index].copy(),
        dist=res_pca.ind.dist.loc[orig_index].copy() if res_pca.ind.dist is not None else None,
    )

    dim_names = list(res_pca.var.coord.columns)
    ncp_eff = len(dim_names)
    var_coord = res_pca.var.coord.to_numpy()  # (n_active × ncp)
    eig_vals = res_pca.eig["eigenvalue"].to_numpy()

    # Per-group factor scores + partial-variable / dimension correlations.
    var_partiel: dict[str, pd.DataFrame] = {}
    cor_dim_gr: dict[str, pd.DataFrame] = {}
    fs: dict[str, np.ndarray] = {}
    for lv in levels:
        mask = fac_codes == lv
        fs_lv = ind_block.coord.loc[don2.index[mask]].to_numpy()
        fs[lv] = fs_lv
        var_partiel[lv] = pd.DataFrame(
            _corr_cols(Xc[lv].to_numpy(), fs_lv), index=xc_labels, columns=dim_names
        )
        cor_dim_gr[lv] = pd.DataFrame(
            _corr_cols(fs_lv, fs_lv), index=dim_names, columns=dim_names
        )

    # Group block: coord[j,s] = v_sᵀ Cov_active_j v_s / λ_s (R/DMFA.R:65-82).
    coord_gr = np.zeros((ng, ncp_eff))
    coord_gr_n = np.zeros((ng, ncp_eff))
    cos2_gr = np.zeros((ng, ncp_eff))
    for j, lv in enumerate(levels):
        cov_active = Cov[lv].to_numpy()[:n_active, :n_active]
        for s in range(ncp_eff):
            v = var_coord[:, s]
            coord_gr[j, s] = float(v @ cov_active @ v) / eig_vals[s]
        eigvals = np.linalg.eigvalsh(cov_active)[::-1]  # descending
        coord_gr_n[j] = coord_gr[j] / eigvals[0]
        cos2_gr[j] = coord_gr[j] ** 2 / float((eigvals**2).sum()) * 100.0

    group_coord = pd.DataFrame(coord_gr, index=levels, columns=dim_names)
    group_coord_n = pd.DataFrame(coord_gr_n, index=levels, columns=dim_names)
    group_cos2 = pd.DataFrame(cos2_gr, index=levels, columns=dim_names)

    return DMFAResult(
        eig=res_pca.eig.copy(),
        svd=res_pca.svd,
        ind=ind_block,
        var=res_pca.var,
        quanti_sup=res_pca.quanti_sup,
        group_coord=group_coord,
        group_coord_n=group_coord_n,
        group_cos2=group_cos2,
        var_partiel=var_partiel,
        cor_dim_gr=cor_dim_gr,
        Cov=Cov,
        Xc=Xc,
        call={
            "num_fact": str(don2.columns[0]),
            "levels": list(levels),
            "scale_unit": scale_unit,
            "ncp": ncp_eff,
            "quanti_sup": list(quanti_pos),
        },
        method="DMFA",
    )
