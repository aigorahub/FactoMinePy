"""Result containers mirroring FactoMineR's ``res`` lists.

R returns lists with ``$``-accessed fields. We use a small set of
``SimpleNamespace``-based holders so ``res.var.coord`` reads naturally in Python
and the same shape can carry any subset of fields a method actually produces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Block:
    """A coordinates / cos² / contributions block (variables or individuals).

    ``cor`` is FactoMineR's ``var$cor`` (variables only). ``dist`` is squared
    distance to origin (FactoMineR's ``ind$dist``). ``v_test`` and ``eta2``
    show up on qualitative blocks (MCA / quali.sup).
    """

    coord: pd.DataFrame
    cos2: pd.DataFrame | None = None
    contrib: pd.DataFrame | None = None
    cor: pd.DataFrame | None = None
    dist: pd.Series | None = None
    inertia: pd.Series | None = None
    v_test: pd.DataFrame | None = None
    eta2: pd.DataFrame | None = None
    # MFA's per-group partial coordinates (``res$ind$coord.partiel``): an
    # ``(n·K) × ncp`` frame with one row per (individual, group) pair.
    coord_partiel: pd.DataFrame | None = None


@dataclass(frozen=True)
class MFAGroup:
    """MFA's ``res$group`` slot — the groups-of-variables block.

    ``coord``/``contrib``/``cos2`` are ``K × ncp`` (one row per active group);
    ``dist2`` is a length-``K`` Series; ``correlation`` is ``K × ncp`` (partial
    group axes vs the global axes, A2 scope). ``Lg`` and ``RV`` are
    ``(K+1) × (K+1)`` matrices whose last row/column is the global ``"MFA"``
    configuration. Mirrors FactoMineR ``MFA(...)$group``.
    """

    coord: pd.DataFrame
    contrib: pd.DataFrame | None = None
    cos2: pd.DataFrame | None = None
    dist2: pd.Series | None = None
    correlation: pd.DataFrame | None = None
    Lg: pd.DataFrame | None = None
    RV: pd.DataFrame | None = None


@dataclass(frozen=True)
class SVD:
    vs: np.ndarray  # singular values
    U: np.ndarray   # left singular vectors (rows × ncp)
    V: np.ndarray   # right singular vectors (cols × ncp)


@dataclass(frozen=True)
class Result:
    """FactoMineR-shaped result object.

    Only ``eig``, ``svd``, ``call`` are always present. Method-specific blocks
    are attached as additional attributes — ``ind`` and ``var`` for PCA; ``row``
    and ``col`` for CA; etc.
    """

    eig: pd.DataFrame
    svd: SVD
    call: dict[str, Any] = field(default_factory=dict)
    ind: Block | None = None
    var: Block | None = None
    row: Block | None = None
    col: Block | None = None
    ind_sup: Block | None = None
    quanti_sup: Block | None = None
    quali_sup: Block | None = None
    row_sup: Block | None = None
    col_sup: Block | None = None
    quanti_var_sup: Block | None = None
    # FAMD splits the variable description into a continuous block
    # (``quanti_var``) and a categorical block (``quali_var``), mirroring
    # R FactoMineR's ``res$quanti.var`` / ``res$quali.var``. ``var`` carries
    # the combined summary (squared loadings for quanti, eta² for quali).
    quanti_var: Block | None = None
    quali_var: Block | None = None
    # MFA's groups-of-variables block (coord/contrib/cos2/dist2/correlation/Lg/RV).
    group: MFAGroup | None = None
    # MFA's ``res$partial.axes`` — correlations/coords/contribs of each group's
    # separate principal axes with the global axes (a ``coord``/``cor``/``contrib``
    # Block), and ``res$inertia.ratio`` — the per-axis between/total inertia ratio.
    partial_axes: Block | None = None
    inertia_ratio: pd.Series | None = None
    # Method tag for ``summary()``: "PCA", "CA", "MCA", ...
    method: str = ""

    def summary(self, ncp: int | None = None) -> str:
        ncp = ncp if ncp is not None else min(5, self.eig.shape[0])
        lines: list[str] = []
        lines.append(f"\nResults for the {self.method or 'analysis'}")
        lines.append("=" * 50)
        lines.append("\nEigenvalues")
        lines.append("-" * 50)
        eig = self.eig.head(ncp).copy()
        eig.columns = ["eigenvalue", "percentage of variance", "cumulative percentage of variance"]
        lines.append(eig.round(4).to_string())

        for label, block in [
            ("Individuals", self.ind),
            ("Variables", self.var),
            ("Rows", self.row),
            ("Columns", self.col),
        ]:
            if block is None:
                continue
            lines.append(f"\n{label} (the first {min(ncp, block.coord.shape[0])} are reported)")
            lines.append("-" * 50)
            head = block.coord.iloc[: min(10, block.coord.shape[0]), :ncp].copy()
            head.columns = [f"Dim.{i + 1}" for i in range(head.shape[1])]
            lines.append(head.round(4).to_string())

        for label, block in [
            ("Supplementary individuals", self.ind_sup),
            ("Supplementary continuous variables", self.quanti_sup),
            ("Supplementary categories", self.quali_sup),
            ("Supplementary rows", self.row_sup),
            ("Supplementary columns", self.col_sup),
        ]:
            if block is None or block.coord.empty:
                continue
            lines.append(f"\n{label}")
            lines.append("-" * 50)
            head = block.coord.iloc[: min(10, block.coord.shape[0]), :ncp].copy()
            head.columns = [f"Dim.{i + 1}" for i in range(head.shape[1])]
            lines.append(head.round(4).to_string())

        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"<factominer.{self.method or 'Result'} ncp={self.eig.shape[0]}>"
