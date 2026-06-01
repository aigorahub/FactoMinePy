"""Multiple Factor Analysis — FactoMineR-compatible.

Ported from R FactoMineR 2.14 ``R/MFA.R`` for the active-groups case with
uniform row weights. Group types ``"s"`` (standardized quantitative), ``"c"``
(centered quantitative), and ``"n"`` (categorical) are supported; ``"f"`` /
``"m"`` raise :class:`NotImplementedError` (no parity fixture exercises them
yet — see ROADMAP / the run-2 plan).

MFA is a single **global weighted PCA** on the horizontal concatenation of all
groups, where each group's columns are weighted by ``1/λ₁`` — the inverse of
the first eigenvalue of that group's *separate* analysis (PCA for quantitative
groups, MCA for categorical) — so that no single group dominates the global
axes (each group's leading axis carries inertia 1). The global eigen-step is
delegated to :func:`factominer.PCA` (``scale_unit=False``,
``col_w=ponderation``), exactly as R delegates to ``FactoMineR::PCA``. This
module:

1. runs each group's separate analysis to recover ``λ₁`` (and the separate
   eigenvalue spectrum, used for ``group$dist2``/``cos2``);
2. assembles the standardized data matrix and the per-column weight vector
   (``ponderation``);
3. calls the weighted PCA, appending the raw categorical factors as
   ``quali.sup`` so category coordinates come out as supplementary barycenters;
4. post-processes the global result into MFA's ``ind`` / ``quanti.var`` /
   ``quali.var`` / ``group`` blocks.

Conventions matched to R (``R/MFA.R`` line refs):

- per-group column weight = ``1/λ₁`` for quantitative groups (L239). For a
  categorical group, category ``k``'s weight is ``(1 − p_k)/(λ₁·J)`` where
  ``J`` = number of variables in the group and ``p_k`` the category proportion
  (L261).
- a categorical column enters the global matrix as a *standardized* centered
  indicator ``(1[i∈k] − p_k)/√(p_k(1 − p_k))`` (L262–269) — NOT FAMD's
  ``1/√p_k`` scaling; the difference is absorbed by the column weight.
- ``eig`` is truncated to ``ncp.tmp = min(n−1, ncol(data) − Σ #vars in "n"
  groups)`` (L350, L636); percentages stay relative to the full global inertia.
- ``quali.var`` coord/cos2/v.test come from the global PCA's ``quali.sup``
  barycenters; ``quali.var$contrib`` is the active indicator columns'
  contribution copied by modality name (L662–667).
- ``group$coord = (group's contribution-fraction to axis k) × eigenvalue_k``
  (L406–416); ``group$dist2 = diag(Lg)``; ``group$Lg`` via the ``funcLg``
  kernel (L9–25, L430–456); ``group$RV`` = ``Lg`` normalized by ``√diag(Lg)``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

from ._result import Block, MFAGroup, Result
from .mca import MCA
from .pca import PCA

_QUANTI_TYPES = {"s", "c"}
_SUPPORTED_TYPES = {"s", "c", "n"}


def _weighted_corr(a: np.ndarray, b: np.ndarray, w: np.ndarray) -> float:
    """Weighted (ML / population) Pearson correlation — matches R's
    ``cov.wt(cbind(a, b), wt, method="ML", cor=TRUE)$cor[1,2]``."""
    w = w / w.sum()
    da = a - float((a * w).sum())
    db = b - float((b * w).sum())
    cov = float((w * da * db).sum())
    va = float((w * da * da).sum())
    vb = float((w * db * db).sum())
    return cov / np.sqrt(va * vb) if va > 0 and vb > 0 else 0.0


def _modality_label(var: str, level: str) -> str:
    """R ``tab.disjonctif`` modality naming: the bare category level, except
    levels that are exactly ``y``/``n``/``Y``/``N`` get the variable name
    prefixed (``<var>.<level>``) to keep them distinguishable."""
    if level in ("y", "n", "Y", "N"):
        return f"{var}.{level}"
    return level


def MFA(  # noqa: N802 — mirrors R's function name
    X: pd.DataFrame,
    group: list[int],
    type: list[str] | None = None,  # noqa: A002 — mirrors R's ``type`` argument
    ncp: int = 5,
    name_group: list[str] | None = None,
    num_group_sup: list[int] | None = None,
    graph: bool = False,  # noqa: ARG001 — accepted for FactoMineR compatibility
) -> Result:
    """Run Multiple Factor Analysis on a table partitioned into groups.

    Mirrors ``FactoMineR::MFA`` for the active-group case with uniform row
    weights. ``group`` gives the column count of each consecutive group;
    ``type`` gives each group's kind (``"s"`` standardized-quantitative,
    ``"c"`` centered-quantitative, ``"n"`` categorical). Returns a
    :class:`Result` with ``eig``, ``ind``, ``quanti_var``, ``quali_var``,
    ``group`` (groups-of-variables block with ``Lg``/``RV``), and ``svd``.
    """
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X must be a pandas DataFrame")
    group = [int(g) for g in group]
    if any(g <= 0 for g in group):
        raise ValueError("each group size must be a positive integer")
    if sum(group) != X.shape[1]:
        raise ValueError(
            f"sum(group)={sum(group)} must equal the number of columns {X.shape[1]}"
        )
    nbre_group = len(group)
    if type is None:
        type = ["s"] * nbre_group
    if len(type) != nbre_group:
        raise ValueError("type must have one entry per group")
    if num_group_sup is not None:
        raise NotImplementedError(
            "supplementary groups (num_group_sup) are not yet implemented; "
            "they are scheduled for the MFA-completeness batch."
        )
    if name_group is None:
        name_group = [f"Gr{i + 1}" for i in range(nbre_group)]
    if len(name_group) != nbre_group:
        raise ValueError("name_group must have one entry per group")

    n = X.shape[0]
    if n < 3:
        raise ValueError("MFA needs at least 3 rows")
    rw = np.full(n, 1.0 / n)  # uniform row weights (R's row.w, normalized)

    # Column slice [start, end) of each group within X.
    col_ranges: list[tuple[int, int]] = []
    off = 0
    for g in group:
        col_ranges.append((off, off + g))
        off += g

    data_blocks: list[np.ndarray] = []  # standardized columns entering the global PCA
    col_labels: list[str] = []          # label of each global-PCA active column
    ponderation: list[float] = []       # per-column weight (col.w)
    quanti_labels: list[str] = []       # active quantitative column labels
    quali_modality_labels: list[str] = []  # active categorical modality labels
    factor_cols: list[str] = []         # raw categorical column names (for quali.sup)
    data_cols_of_group: list[list[int]] = []  # global-PCA column indices per group
    lam1: list[float] = []              # first separate eigenvalue per group
    dist2_sep: list[float] = []         # Σ(λ_l/λ₁)² per group (separate spectrum)
    separate: list[Result] = []         # each group's separate analysis (for partial.axes)

    col_cursor = 0
    for g, (start, end) in enumerate(col_ranges):
        t = type[g]
        block = X.iloc[:, start:end]
        cols = list(block.columns)
        if t not in _SUPPORTED_TYPES:
            raise NotImplementedError(
                f"MFA group type {t!r} is not yet supported (only "
                f"{sorted(_SUPPORTED_TYPES)}); frequency/mixed groups are "
                f"scheduled for a later batch."
            )

        group_cols_start = col_cursor
        if t in _QUANTI_TYPES:
            if not all(is_numeric_dtype(block[c].dtype) for c in cols):
                raise ValueError(f"group {g + 1} is type {t!r} but has non-numeric columns")
            Q = block.to_numpy(dtype=np.float64)
            sep = PCA(block, scale_unit=(t == "s"))
            separate.append(sep)
            sep_eig = sep.eig["eigenvalue"].to_numpy()
            lam1.append(float(sep_eig[0]))
            dist2_sep.append(float(((sep_eig / sep_eig[0]) ** 2).sum()))
            if t == "s":
                centre = (Q * rw[:, None]).sum(axis=0)
                Qc = Q - centre
                sd = np.sqrt((Qc**2 * rw[:, None]).sum(axis=0))
                sd = np.where(sd <= 1e-8, 1.0, sd)  # R/MFA.R:233
                block_arr = Qc / sd
            else:  # "c": enter raw; the global PCA centers (scale_unit=False)
                block_arr = Q
            data_blocks.append(block_arr)
            for c in cols:
                col_labels.append(str(c))
                quanti_labels.append(str(c))
                ponderation.append(1.0 / lam1[g])
                col_cursor += 1
        else:  # type "n" — categorical
            block_cat = block.copy()
            for c in cols:
                block_cat[c] = block_cat[c].astype("category")
            sep = MCA(block_cat)
            separate.append(sep)
            sep_eig = sep.eig["eigenvalue"].to_numpy()
            lam1.append(float(sep_eig[0]))
            dist2_sep.append(float(((sep_eig / sep_eig[0]) ** 2).sum()))
            J = len(cols)
            for c in cols:
                factor_cols.append(str(c))
                col = block_cat[c]
                for cat in col.cat.categories:
                    indicator = (col == cat).to_numpy(dtype=np.float64)
                    p = float((indicator * rw).sum())  # category proportion
                    sd = np.sqrt(p * (1.0 - p))
                    sd = sd if sd > 1e-8 else 1.0  # R/MFA.R:268 (degenerate category)
                    z = (indicator - p) / sd
                    data_blocks.append(z[:, None])
                    label = _modality_label(str(c), str(cat))
                    col_labels.append(label)
                    quali_modality_labels.append(label)
                    ponderation.append((1.0 - p) / (lam1[g] * J))
                    col_cursor += 1
        data_cols_of_group.append(list(range(group_cols_start, col_cursor)))

    if len(set(col_labels)) != len(col_labels):
        raise ValueError(
            "MFA produced colliding active-column labels; this happens when two "
            "categorical modalities share a bare level name. Disambiguation for "
            "this case is not yet implemented."
        )

    data = np.hstack(data_blocks)
    n_data_cols = data.shape[1]
    ponderation_arr = np.asarray(ponderation, dtype=np.float64)

    # Assemble the data frame for the global PCA: active standardized columns
    # plus the raw categorical factors appended as supplementary qualitatives
    # (so category coordinates come out as supplementary barycenters, as in R).
    data_df = pd.DataFrame(data, index=X.index, columns=col_labels)
    pca_frame = data_df
    quali_sup_positions: list[int] | None = None
    if factor_cols:
        raw_factors = X[factor_cols].copy()
        pca_frame = pd.concat([data_df, raw_factors], axis=1)
        quali_sup_positions = list(range(n_data_cols, n_data_cols + len(factor_cols)))
    col_w_full = np.concatenate([ponderation_arr, np.ones(len(factor_cols))])

    pca = PCA(
        pca_frame,
        scale_unit=False,
        ncp=ncp,
        col_w=col_w_full,
        quali_sup=quali_sup_positions,
    )

    # eig: truncate to ncp.tmp, keeping the global PCA's percentages (R/MFA.R:350,636).
    n_quali_vars = sum(group[g] for g in range(nbre_group) if type[g] == "n")
    ncp_tmp = int(min(n - 1, n_data_cols - n_quali_vars))
    eig = pca.eig.iloc[:ncp_tmp].copy()

    ncp_eff = int(min(ncp, pca.eig.shape[0]))
    dim_names = list(pca.ind.coord.columns[:ncp_eff])
    eig_vals = pca.eig["eigenvalue"].to_numpy()
    n_ind = data.shape[0]
    K = nbre_group  # number of active groups (all active in this case)

    # --- partial individual coordinates (R/MFA.R:458-477) ---
    # For group g, project the individuals using ONLY group g's centered columns
    # (every other group held at the global mean), scaled by K, onto the global
    # axes: data.partiel = broadcast centre with group g's columns = data, so
    # Xis = data.partiel − centre has group g centered and all other groups 0.
    # coord = K·(Xis·col.w)·V_unwhitened = K·(Xis·√col.w)·V_tilde (pca.svd.V is
    # the whitened V_tilde, so the √col.w factor restores R's unwhitened V).
    centre = np.asarray(pca.call["mean"], dtype=np.float64)
    col_w_active = np.asarray(pca.call["col_w"], dtype=np.float64)
    v_tilde = pca.svd.V[:, :ncp_eff]
    sqrt_cw = np.sqrt(col_w_active)
    data_centered = data - centre
    partial_coords: list[np.ndarray] = []  # K arrays, each (n × ncp_eff)
    for g in range(nbre_group):
        xis = np.zeros_like(data)
        idx = data_cols_of_group[g]
        xis[:, idx] = data_centered[:, idx]
        partial_coords.append(K * (xis * sqrt_cw[None, :]) @ v_tilde)
    # Assemble (n·K) × ncp, rows interleaved by individual (R's nom.ligne order:
    # ind_1.group_1, ind_1.group_2, …, ind_1.group_K, ind_2.group_1, …).
    ind_names = [str(x) for x in X.index]
    coord_partiel_arr = np.empty((n_ind * nbre_group, ncp_eff))
    partiel_labels: list[str] = []
    for i in range(n_ind):
        for g in range(nbre_group):
            coord_partiel_arr[i * nbre_group + g] = partial_coords[g][i]
            partiel_labels.append(f"{ind_names[i]}.{name_group[g]}")
    coord_partiel = pd.DataFrame(coord_partiel_arr, index=partiel_labels, columns=dim_names)

    # --- ind: straight from the global PCA (+ coord.partiel). R MFA's res$ind
    #     exposes coord/contrib/cos2/coord.partiel (and within.inertia, deferred);
    #     it has no `dist`, so we don't surface one either (schema parity). ---
    ind_block = Block(
        coord=pca.ind.coord[dim_names].copy(),
        cos2=pca.ind.cos2[dim_names].copy(),
        contrib=pca.ind.contrib[dim_names].copy(),
        coord_partiel=coord_partiel,
    )

    # --- quanti.var: the quantitative active columns of the global var block ---
    quanti_var = None
    if quanti_labels:
        quanti_var = Block(
            coord=pca.var.coord.loc[quanti_labels, dim_names].copy(),
            cos2=pca.var.cos2.loc[quanti_labels, dim_names].copy(),
            contrib=pca.var.contrib.loc[quanti_labels, dim_names].copy(),
            cor=pca.var.cor.loc[quanti_labels, dim_names].copy()
            if pca.var.cor is not None
            else None,
        )

    # --- quali.var: coord/cos2/v.test from quali.sup barycenters; contrib from
    #     the active indicator columns (R/MFA.R:662–667) ---
    quali_var = None
    if quali_modality_labels and pca.quali_sup is not None:
        def _relabel(df: pd.DataFrame) -> pd.DataFrame:
            new_index = []
            for lbl in df.index:
                var, _, level = str(lbl).partition("=")
                new_index.append(_modality_label(var, level))
            out = df.copy()
            out.index = new_index
            return out

        coord_q = _relabel(pca.quali_sup.coord)[dim_names]
        order = list(coord_q.index)
        cos2_q = _relabel(pca.quali_sup.cos2).loc[order, dim_names]
        vtest_q = _relabel(pca.quali_sup.v_test).loc[order, dim_names]
        contrib_q = pca.var.contrib.loc[order, dim_names]
        quali_var = Block(
            coord=coord_q,
            cos2=cos2_q,
            contrib=contrib_q,
            v_test=vtest_q,
        )

    # --- group block (R/MFA.R:406–456) ---
    var_contrib = pca.var.contrib[dim_names].to_numpy()  # active columns × ncp_eff
    contrib_frac = np.zeros((nbre_group, ncp_eff))
    for g in range(nbre_group):
        idx = data_cols_of_group[g]
        contrib_frac[g] = var_contrib[idx, :].sum(axis=0) / 100.0
    coord_group = contrib_frac * eig_vals[None, :ncp_eff]
    dist2_sep_arr = np.asarray(dist2_sep, dtype=np.float64)
    cos2_group = coord_group**2 / dist2_sep_arr[:, None]
    contrib_group = contrib_frac * 100.0

    # Lg via the funcLg kernel: Lg[a,b] = Σ_{j∈a,k∈b} pond_j pond_k cov_w(d_j, d_k)².
    dc = data - (data * rw[:, None]).sum(axis=0)  # weighted-centered active columns
    cov_w = (dc * rw[:, None]).T @ dc             # P×P weighted covariance
    M = np.outer(ponderation_arr, ponderation_arr) * cov_w**2
    Lg = np.zeros((nbre_group + 1, nbre_group + 1))
    for a in range(nbre_group):
        ia = data_cols_of_group[a]
        for b in range(a, nbre_group):
            ib = data_cols_of_group[b]
            val = float(M[np.ix_(ia, ib)].sum())
            Lg[a, b] = Lg[b, a] = val
    lam1_global = float(eig_vals[0])
    Lg[nbre_group, :nbre_group] = Lg[:nbre_group, :nbre_group].sum(axis=0) / lam1_global
    Lg[:nbre_group, nbre_group] = Lg[nbre_group, :nbre_group]
    Lg[nbre_group, nbre_group] = Lg[:nbre_group, nbre_group].sum() / lam1_global
    diag = np.sqrt(np.diag(Lg))
    RV = Lg / diag[:, None] / diag[None, :]
    group_labels = list(name_group) + ["MFA"]
    dist2_group = np.diag(Lg)[:nbre_group]

    # group$correlation (R/MFA.R:478-483): weighted (ML) correlation of each
    # group's partial individual coords with the global coords, per axis.
    global_coord = pca.ind.coord[dim_names].to_numpy()
    cor_grpe = np.zeros((nbre_group, ncp_eff))
    for g in range(nbre_group):
        for k in range(ncp_eff):
            cor_grpe[g, k] = _weighted_corr(partial_coords[g][:, k], global_coord[:, k], rw)

    group_block = MFAGroup(
        coord=pd.DataFrame(coord_group, index=name_group, columns=dim_names),
        contrib=pd.DataFrame(contrib_group, index=name_group, columns=dim_names),
        cos2=pd.DataFrame(cos2_group, index=name_group, columns=dim_names),
        dist2=pd.Series(dist2_group, index=name_group, name="dist2"),
        correlation=pd.DataFrame(cor_grpe, index=name_group, columns=dim_names),
        Lg=pd.DataFrame(Lg, index=group_labels, columns=group_labels),
        RV=pd.DataFrame(RV, index=group_labels, columns=group_labels),
    )

    # --- partial.axes (R/MFA.R:521-554): each group's separate principal axes,
    #     standardized, correlated with the global axes. coord == cor (the tab is
    #     unit-variance, so dividing by its sd is a no-op); contrib is the squared
    #     coord weighted by the group's separate eigenvalue ratio, normalized to
    #     100 per axis. ---
    tab_cols: list[np.ndarray] = []
    pa_labels: list[str] = []
    pa_eig_ratio: list[float] = []
    for g in range(nbre_group):
        sep_coord = separate[g].ind.coord.to_numpy()
        sep_eig_g = separate[g].eig["eigenvalue"].to_numpy()
        nbcol = int(min(ncp_eff, sep_coord.shape[1]))
        for col_l in range(nbcol):
            tab_cols.append(sep_coord[:, col_l])
            pa_labels.append(f"Dim{col_l + 1}.{name_group[g]}")
            pa_eig_ratio.append(float(sep_eig_g[col_l] / sep_eig_g[0]))
    tab = np.column_stack(tab_cols)
    tab_centre = (tab * rw[:, None]).sum(axis=0)
    tab_c = tab - tab_centre
    tab_sd = np.sqrt((tab_c**2 * rw[:, None]).sum(axis=0))
    tab_sd = np.where(tab_sd <= 1e-8, 1.0, tab_sd)
    tab_scaled = tab_c / tab_sd
    u_tilde = pca.svd.U[:, :ncp_eff]
    pa_coord = (tab_scaled * np.sqrt(rw)[:, None]).T @ u_tilde  # (P_axes × ncp_eff)
    pa_sigma = np.sqrt((tab_scaled**2 * rw[:, None]).sum(axis=0))
    pa_sigma = np.where(pa_sigma <= 0, 1.0, pa_sigma)
    pa_cor = pa_coord / pa_sigma[:, None]
    pa_contrib = pa_coord**2 * np.asarray(pa_eig_ratio)[:, None]
    pa_col_sums = pa_contrib.sum(axis=0)
    pa_col_sums = np.where(pa_col_sums <= 0, 1.0, pa_col_sums)
    pa_contrib = pa_contrib / pa_col_sums[None, :] * 100.0
    partial_axes = Block(
        coord=pd.DataFrame(pa_coord, index=pa_labels, columns=dim_names),
        cor=pd.DataFrame(pa_cor, index=pa_labels, columns=dim_names),
        contrib=pd.DataFrame(pa_contrib, index=pa_labels, columns=dim_names),
    )

    # --- inertia.ratio (R/MFA.R:484-486): per-axis between/total inertia ratio. ---
    it = np.zeros(ncp_eff)
    for g in range(nbre_group):
        it += (partial_coords[g] ** 2 * rw[:, None]).sum(axis=0)
    global_inertia = (global_coord**2 * rw[:, None]).sum(axis=0)
    inertia_ratio = pd.Series(global_inertia * K / it, index=dim_names, name="inertia.ratio")

    return Result(
        eig=eig,
        svd=pca.svd,
        call={
            "ncp": ncp_eff,
            "group": list(group),
            "type": list(type),
            "name_group": list(name_group),
            "quanti_labels": list(quanti_labels),
            "quali_modality_labels": list(quali_modality_labels),
            "row_w": rw.copy(),
            "active_frame": X.copy(),
        },
        ind=ind_block,
        quanti_var=quanti_var,
        quali_var=quali_var,
        group=group_block,
        partial_axes=partial_axes,
        inertia_ratio=inertia_ratio,
        method="MFA",
    )
