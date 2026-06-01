"""Hierarchical Multiple Factor Analysis — FactoMineR-compatible.

Ported from R FactoMineR 2.14 ``R/HMFA.R`` for the active-group case with
uniform row weights. HMFA generalizes :func:`factominer.MFA` to a *hierarchy*
of groups: ``H`` is a list with one entry per hierarchical level, ``H[0]`` being
the elementary-group sizes (exactly MFA's ``group``) and ``H[h]`` (``h ≥ 1``)
the number of previous-level groups each level-``h`` node aggregates.

The method reduces to a single weighted PCA on the level-1-standardized data
matrix (R's ``XTDC``), with column weights that accumulate one ``1/λ₁`` factor
per hierarchy level (R's ``hweight``). Concretely, level 1 is an MFA whose
``ponderation`` gives the bottom weights; each higher level re-runs MFA on the
already-standardized ``XTDC`` (all nodes typed ``"c"``) passing the running
weights as ``weight.col.mfa``, then multiplies the new per-node ``1/λ₁`` into the
accumulated weight vector (``HMFA.R`` L51-52 — the keystone). The final
``PCA(XTDC, col.w=poids_top, scale_unit=False)`` *is* the HMFA.

Outputs (matched to R ``HMFA.R`` line refs):

- ``eig``, ``ind`` (coord/cos2/contrib/dist) — straight from the global PCA.
- ``quanti.var`` (coord/cor/cos2/contrib) — the quantitative columns of the
  global ``var`` block (L177-187).
- ``quali.var`` (coord/contrib) — category coordinates as barycenters of the
  individuals carrying each category, with the active-indicator contributions
  (L188-197).
- ``group.coord`` — a **list, one matrix per hierarchy level**; entry ``h`` is
  ``(#nodes × ncp)`` with ``coord[g,k] = Σ_{col∈node g} var.coord[col,k]² ·
  poids[h][col]`` (L104-124).
- ``group.canonical`` — canonical correlations ``diag(cor(global ind coord,
  partial coord_{h,g}))`` stacked over every node of every level (L160-172).
- ``partial`` — a list (per level) of ``(n × ncp × #nodes)`` partial individual
  coordinate arrays (L125-148); plotting-tier, exposed but validated indirectly
  through ``canonical``.

Supported group types: ``"s"`` / ``"c"`` / ``"n"`` (frequency/mixed are not
supported, as in MFA). ``quali.var$partial`` and ``within.inertia`` are not
surfaced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

from ._result import SVD, Block
from .mfa import MFA
from .pca import PCA


@dataclass(frozen=True)
class HMFAResult:
    """FactoMineR ``HMFA``-shaped result.

    ``group_coord`` is a list with one ``(#nodes × ncp)`` frame per hierarchy
    level; ``group_canonical`` stacks the canonical correlations of every node
    of every level. ``partial`` holds the per-level partial-coordinate arrays.
    """

    eig: pd.DataFrame
    svd: SVD
    ind: Block
    quanti_var: Block
    group_coord: list[pd.DataFrame]
    group_canonical: pd.DataFrame
    partial: list[np.ndarray]
    quali_var: Block | None = None
    call: dict[str, Any] = field(default_factory=dict)
    method: str = "HMFA"

    def __repr__(self) -> str:
        return f"<factominer.HMFA levels={len(self.group_coord)} ncp={self.eig.shape[0]}>"


def _htabdes(H: list[list[int]]) -> list[list[int]]:
    """R ``htabdes``: given ``H`` with an already-expanded bottom level, return
    the expanded (XTDC) column count of each node at every level."""
    nbvarh = [list(h) for h in H]
    for i in range(1, len(H)):
        for j in range(len(H[i])):
            start = sum(H[i][:j])
            nbvarh[i][j] = sum(nbvarh[i - 1][start : start + H[i][j]])
    return nbvarh


def _hdil(H: list[list[int]]) -> list[list[int]]:
    """R ``hdil``: per-level dilation factors used to rescale partial coords."""
    nbnivh = len(H)
    dil: list[list[int]] = [list(h) for h in H]
    dil[nbnivh - 1] = [len(H[nbnivh - 1])] * len(H[nbnivh - 1])
    for i in range(1, nbnivh):
        h = nbnivh - 1 - i
        k = h + 1
        a: list[int] = []
        for j in range(len(H[k])):
            a += [H[k][j] * dil[k][j]] * H[k][j]
        dil[h] = a
    return dil


def _hweight(
    X: pd.DataFrame, H: list[list[int]], type: list[str]  # noqa: A002
) -> list[np.ndarray]:
    """R ``hweight``: the accumulated per-column weights, one vector per level.

    Level 1 is a plain MFA (its ``col.w`` is the bottom weight); each higher
    level re-runs MFA on the standardized ``XTDC`` with ``weight.col.mfa`` set to
    the running weights, then multiplies in the new per-node ``1/λ₁``.
    """
    niv1 = MFA(X, group=H[0], type=type)
    cw = np.asarray(niv1.call["col_w"], dtype=np.float64)
    Hq: list[list[int]] = [list(niv1.call["group_mod"])] + [list(h) for h in H[1:]]
    hinter = _htabdes(Hq)
    xtdc = niv1.call["XTDC"]
    cw_partiel: list[np.ndarray] = [cw.copy()]
    for n in range(1, len(Hq)):
        niv2 = MFA(
            xtdc,
            group=hinter[n],
            type=["c"] * len(hinter[n]),
            weight_col_mfa=cw,
        )
        cw = np.asarray(niv2.call["col_w"], dtype=np.float64) * cw
        cw_partiel.append(cw.copy())
    return cw_partiel


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    """Unweighted Pearson correlation (R's ``cor`` default)."""
    ac = a - a.mean()
    bc = b - b.mean()
    denom = np.sqrt(float((ac * ac).sum()) * float((bc * bc).sum()))
    return float((ac * bc).sum() / denom) if denom > 0 else 0.0


def HMFA(  # noqa: N802 — mirrors R's function name
    X: pd.DataFrame,
    H: list[list[int]],
    type: list[str] | None = None,  # noqa: A002 — mirrors R's ``type`` argument
    ncp: int = 5,
    name_group: list[list[str]] | None = None,
    graph: bool = False,  # noqa: ARG001 — accepted for FactoMineR compatibility
) -> HMFAResult:
    """Run Hierarchical Multiple Factor Analysis.

    Mirrors ``FactoMineR::HMFA`` for active groups with uniform row weights.
    ``H`` is a list of per-level group counts (``H[0]`` = elementary group
    sizes, ``H[h≥1]`` = #previous-level groups per level-``h`` node); ``type``
    has one entry per elementary group (``"s"``/``"c"``/``"n"``).
    """
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X must be a pandas DataFrame")
    if not H or not all(isinstance(level, (list, tuple)) for level in H):
        raise ValueError("H must be a non-empty list of per-level group-count lists")
    H = [[int(x) for x in level] for level in H]
    if sum(H[0]) != X.shape[1]:
        raise ValueError(f"sum(H[0])={sum(H[0])} must equal the column count {X.shape[1]}")
    for lvl in range(1, len(H)):
        if sum(H[lvl]) != len(H[lvl - 1]):
            raise ValueError(
                f"sum(H[{lvl}])={sum(H[lvl])} must equal the number of level-{lvl - 1} "
                f"groups {len(H[lvl - 1])}"
            )
    if type is None:
        type = ["s"] * len(H[0])
    if len(type) != len(H[0]):
        raise ValueError("type must have one entry per elementary group (H[0])")

    nbnivo = len(H)
    nbind = X.shape[0]

    # Accumulated per-level column weights (the keystone).
    poids = _hweight(X, H, type)

    # Center numeric columns (R/HMFA.R:74-76) before the final analysis — a
    # no-op for "s" (re-standardized) and "c" (the global PCA re-centers), but
    # kept for faithfulness.
    Xc = X.copy()
    for j in Xc.columns:
        if is_numeric_dtype(Xc[j].dtype):
            Xc[j] = Xc[j] - Xc[j].mean()
    niv1 = MFA(Xc, group=H[0], type=type, ncp=ncp)
    xtdc = niv1.call["XTDC"]
    group_mod = list(niv1.call["group_mod"])
    Hq: list[list[int]] = [list(group_mod)] + [list(h) for h in H[1:]]
    xdes = _htabdes(Hq)

    # Expanded-column indices of the categorical (type "n") elementary groups.
    ind_quali: list[int] = []
    ind_var = 0
    for g in range(len(H[0])):
        if type[g] == "n":
            ind_quali += list(range(ind_var, ind_var + group_mod[g]))
        ind_var += group_mod[g]

    xt = xtdc.to_numpy()
    n_cols = xt.shape[1]

    # res1[h][g]: XTDC with only node g's columns kept (others zeroed).
    res1: list[list[np.ndarray]] = []
    for h in range(nbnivo):
        data_partiel: list[np.ndarray] = []
        ind_col = 0
        for g in range(len(H[h])):
            m = np.zeros((nbind, n_cols))
            m[:, ind_col : ind_col + xdes[h][g]] = xt[:, ind_col : ind_col + xdes[h][g]]
            data_partiel.append(m)
            ind_col += xdes[h][g]
        res1.append(data_partiel)

    # The HMFA is one weighted PCA on XTDC with the top-level accumulated weights.
    res_afmh = PCA(xtdc, col_w=poids[nbnivo - 1], scale_unit=False, ncp=ncp)
    dilat = _hdil(H)
    nb_vp = res_afmh.ind.coord.shape[1]
    dim_names = list(res_afmh.ind.coord.columns)
    ind_coord = res_afmh.ind.coord.to_numpy()
    var_coord = res_afmh.var.coord.to_numpy()
    eig_vals = res_afmh.eig["eigenvalue"].to_numpy()

    def _level_labels(h: int, nbgroup: int) -> list[str]:
        if name_group is not None:
            return list(name_group[h])
        return [f"L{h + 1}.G{g + 1}" for g in range(nbgroup)]

    # group$coord per level: per-node sum of poids[h]-weighted squared var coords.
    group_coord: list[pd.DataFrame] = []
    for h in range(nbnivo):
        weighted = var_coord**2 * np.asarray(poids[h], dtype=np.float64)[:, None]
        nbgroup = len(H[h])
        aux = np.zeros((nbgroup, nb_vp))
        ind_col = 0
        for g in range(nbgroup):
            gm = xdes[h][g]
            aux[g] = weighted[ind_col : ind_col + gm].sum(axis=0)
            ind_col += gm
        group_coord.append(pd.DataFrame(aux, index=_level_labels(h, nbgroup), columns=dim_names))

    # Partial individual coordinates per level (R/HMFA.R:130-148).
    partial: list[np.ndarray] = []
    for h in range(nbnivo):
        nbgroup = len(H[h])
        part2 = np.zeros((nbind, nb_vp, nbgroup))
        for g in range(nbgroup):
            formule = res1[h][g] * np.asarray(poids[nbnivo - 1], dtype=np.float64)[None, :]
            formule = formule @ xt.T
            formule = formule / nbind
            formule = formule @ ind_coord
            formule = formule / (eig_vals[:nb_vp] / dilat[h][g])[None, :]
            part2[:, :, g] = formule
        partial.append(part2)

    # Canonical correlations: diag(cor(global ind coord, partial coord)) per node.
    canon_rows: list[np.ndarray] = []
    canon_labels: list[str] = []
    for h in range(nbnivo):
        nbgroup = len(H[h])
        for g in range(nbgroup):
            pg = partial[h][:, :, g]
            canon_rows.append(np.array([_corr(ind_coord[:, k], pg[:, k]) for k in range(nb_vp)]))
        canon_labels += _level_labels(h, nbgroup)
    group_canonical = pd.DataFrame(np.vstack(canon_rows), index=canon_labels, columns=dim_names)

    # ind / quanti.var / quali.var.
    ind_block = Block(
        coord=res_afmh.ind.coord.copy(),
        cos2=res_afmh.ind.cos2.copy(),
        contrib=res_afmh.ind.contrib.copy(),
        dist=res_afmh.ind.dist.copy() if res_afmh.ind.dist is not None else None,
    )

    quanti_rows = [i for i in range(n_cols) if i not in set(ind_quali)]
    var_labels = list(res_afmh.var.coord.index)
    quanti_labels = [var_labels[i] for i in quanti_rows]
    quanti_var = Block(
        coord=res_afmh.var.coord.loc[quanti_labels].copy(),
        cor=res_afmh.var.cor.loc[quanti_labels].copy() if res_afmh.var.cor is not None else None,
        cos2=res_afmh.var.cos2.loc[quanti_labels].copy(),
        contrib=res_afmh.var.contrib.loc[quanti_labels].copy(),
    )

    quali_var = None
    if ind_quali:
        quali_labels = [var_labels[i] for i in ind_quali]
        coord_q = np.zeros((len(ind_quali), nb_vp))
        for k, col in enumerate(ind_quali):
            mask = xt[:, col] > 0  # standardized indicator > 0 ⟺ category present
            coord_q[k] = ind_coord[mask].mean(axis=0)
        quali_var = Block(
            coord=pd.DataFrame(coord_q, index=quali_labels, columns=dim_names),
            contrib=res_afmh.var.contrib.loc[quali_labels].copy(),
        )

    return HMFAResult(
        eig=res_afmh.eig.copy(),
        svd=res_afmh.svd,
        ind=ind_block,
        quanti_var=quanti_var,
        quali_var=quali_var,
        group_coord=group_coord,
        group_canonical=group_canonical,
        partial=partial,
        call={
            "H": [list(h) for h in H],
            "type": list(type),
            "ncp": ncp,
            "group_mod": group_mod,
            "xdes": xdes,
            "name_group": name_group,
        },
        method="HMFA",
    )
