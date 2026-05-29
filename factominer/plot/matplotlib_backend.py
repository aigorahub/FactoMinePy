"""Matplotlib backend reproducing FactoMineR's ``plot.*`` family."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from scipy.cluster.hierarchy import dendrogram

from .._result import Result
from ..hcpc import HCPCResult
from ._data import coord_ellipse

DEFAULT_PALETTE = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
    "#bcbd22", "#17becf",
]


def plot(
    res: Result | HCPCResult,
    choix: str = "ind",
    axes: tuple[int, int] = (0, 1),
    habillage: str | pd.Series | None = None,
    invisible: Iterable[str] | None = None,
    ax: Axes | None = None,
    title: str | None = None,
    ellipse: bool = False,
    ellipse_level: float = 0.95,
) -> Axes:
    """High-level entry point matching ``plot.PCA`` / ``plot.CA`` / ``plot.MCA`` / ``plot.HCPC``.

    ``choix`` controls what is rendered: ``"ind"`` (individuals factor map), ``"var"``
    (variables / correlation circle), ``"biplot"``, ``"scree"``, ``"contrib"``,
    ``"dendrogram"``. Method-specific renderers handle the details.
    """
    invisible = set(invisible or [])
    if isinstance(res, HCPCResult):
        if choix == "dendrogram":
            return plot_hcpc(res, kind="dendrogram", ax=ax, title=title)
        if choix == "factor_map":
            return plot_hcpc(res, kind="factor_map", axes=axes, ax=ax, title=title)
        raise ValueError(f"unsupported choix for HCPC: {choix!r}")

    if choix == "scree":
        return plot_scree(res, ax=ax, title=title)
    if choix == "contrib":
        return plot_contrib(res, axis=axes[0], ax=ax, title=title)
    if choix == "ind":
        if res.method == "MCA":
            return plot_mca(res, kind="ind", axes=axes, habillage=habillage, invisible=invisible,
                            ax=ax, title=title)
        if res.method == "CA":
            return plot_ca(res, kind="row", axes=axes, invisible=invisible, ax=ax, title=title)
        return plot_pca_ind(res, axes=axes, habillage=habillage, invisible=invisible,
                            ellipse=ellipse, ellipse_level=ellipse_level, ax=ax, title=title)
    if choix == "var":
        if res.method == "MCA":
            return plot_mca(res, kind="var", axes=axes, invisible=invisible, ax=ax, title=title)
        if res.method == "CA":
            return plot_ca(res, kind="col", axes=axes, invisible=invisible, ax=ax, title=title)
        return plot_pca_var(res, axes=axes, invisible=invisible, ax=ax, title=title)
    if choix == "biplot":
        if res.method == "PCA":
            return plot_pca_biplot(res, axes=axes, habillage=habillage, ax=ax, title=title)
        if res.method == "CA":
            return plot_ca(res, kind="biplot", axes=axes, ax=ax, title=title)
        if res.method == "MCA":
            return plot_mca(res, kind="biplot", axes=axes, ax=ax, title=title)
    raise ValueError(f"unsupported choix: {choix!r}")


# -- PCA --------------------------------------------------------------------

def plot_pca_ind(
    res: Result,
    axes: tuple[int, int] = (0, 1),
    habillage: str | pd.Series | None = None,
    invisible: set[str] | None = None,
    ellipse: bool = False,
    ellipse_level: float = 0.95,
    ax: Axes | None = None,
    title: str | None = None,
) -> Axes:
    if ax is None:
        import matplotlib.pyplot as plt
        _, ax = plt.subplots(figsize=(7, 6))
    invisible = invisible or set()
    coord = res.ind.coord.iloc[:, list(axes)]
    colors = _resolve_colors(coord.shape[0], habillage, res)
    if "ind" not in invisible:
        ax.scatter(coord.iloc[:, 0], coord.iloc[:, 1], c=colors, s=30, edgecolor="white", linewidth=0.5)
        for label, (x, y) in zip(coord.index, coord.to_numpy(), strict=True):
            ax.annotate(str(label), (x, y), fontsize=8, alpha=0.85)
    if ellipse and habillage is not None:
        _draw_confidence_ellipses(ax, coord, habillage, res, level=ellipse_level, colors=colors)
    if "ind.sup" not in invisible and res.ind_sup is not None:
        sup_coord = res.ind_sup.coord.iloc[:, list(axes)]
        ax.scatter(sup_coord.iloc[:, 0], sup_coord.iloc[:, 1], marker="^", c="dimgray", s=40)
        for label, (x, y) in zip(sup_coord.index, sup_coord.to_numpy(), strict=True):
            ax.annotate(str(label), (x, y), fontsize=8, alpha=0.85, color="dimgray")
    if "quali.sup" not in invisible and res.quali_sup is not None:
        qs = res.quali_sup.coord.iloc[:, list(axes)]
        ax.scatter(qs.iloc[:, 0], qs.iloc[:, 1], marker="s", c="darkred", s=50)
        for label, (x, y) in zip(qs.index, qs.to_numpy(), strict=True):
            ax.annotate(str(label), (x, y), fontsize=8, color="darkred", weight="bold")
    _axis_decoration(ax, res, axes, title or "Individuals factor map (PCA)")
    return ax


def plot_pca_var(
    res: Result,
    axes: tuple[int, int] = (0, 1),
    invisible: set[str] | None = None,
    ax: Axes | None = None,
    title: str | None = None,
) -> Axes:
    if ax is None:
        import matplotlib.pyplot as plt
        _, ax = plt.subplots(figsize=(6, 6))
    invisible = invisible or set()
    coord = res.var.coord.iloc[:, list(axes)]
    # Correlation circle
    theta = np.linspace(0, 2 * np.pi, 256)
    ax.plot(np.cos(theta), np.sin(theta), color="lightgray", lw=1)
    ax.axhline(0, color="lightgray", lw=0.5)
    ax.axvline(0, color="lightgray", lw=0.5)
    if "var" not in invisible:
        for label, (x, y) in zip(coord.index, coord.to_numpy(), strict=True):
            ax.annotate("", xy=(x, y), xytext=(0, 0),
                        arrowprops=dict(arrowstyle="->", color="#1f77b4", lw=1.0))
            ax.annotate(str(label), (x, y), fontsize=9, color="#1f77b4")
    if "quanti.sup" not in invisible and res.quanti_sup is not None:
        qs = res.quanti_sup.coord.iloc[:, list(axes)]
        for label, (x, y) in zip(qs.index, qs.to_numpy(), strict=True):
            ax.annotate("", xy=(x, y), xytext=(0, 0),
                        arrowprops=dict(arrowstyle="->", color="darkgreen", lw=1.0, linestyle="--"))
            ax.annotate(str(label), (x, y), fontsize=9, color="darkgreen")
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.set_aspect("equal")
    _axis_decoration(ax, res, axes, title or "Variables factor map (PCA)")
    return ax


def plot_pca_biplot(
    res: Result,
    axes: tuple[int, int] = (0, 1),
    habillage: str | pd.Series | None = None,
    ax: Axes | None = None,
    title: str | None = None,
) -> Axes:
    if ax is None:
        import matplotlib.pyplot as plt
        _, ax = plt.subplots(figsize=(7, 6))
    coord = res.ind.coord.iloc[:, list(axes)]
    colors = _resolve_colors(coord.shape[0], habillage, res)
    ax.scatter(coord.iloc[:, 0], coord.iloc[:, 1], c=colors, s=30, edgecolor="white", linewidth=0.5)
    # Scale variable arrows to roughly match the spread of individuals
    var = res.var.coord.iloc[:, list(axes)].to_numpy()
    scale = float(np.max(np.abs(coord.to_numpy()))) / max(1e-12, float(np.max(np.abs(var))))
    for label, (x, y) in zip(res.var.coord.index, var * scale, strict=True):
        ax.annotate("", xy=(x, y), xytext=(0, 0),
                    arrowprops=dict(arrowstyle="->", color="darkred", lw=1.0))
        ax.annotate(str(label), (x, y), fontsize=8, color="darkred")
    _axis_decoration(ax, res, axes, title or "PCA biplot")
    return ax


# -- CA / MCA ---------------------------------------------------------------

def plot_ca(
    res: Result,
    kind: str = "biplot",
    axes: tuple[int, int] = (0, 1),
    invisible: set[str] | None = None,
    ax: Axes | None = None,
    title: str | None = None,
) -> Axes:
    if ax is None:
        import matplotlib.pyplot as plt
        _, ax = plt.subplots(figsize=(7, 6))
    invisible = invisible or set()
    if kind in {"row", "biplot"} and "row" not in invisible:
        coord = res.row.coord.iloc[:, list(axes)]
        ax.scatter(coord.iloc[:, 0], coord.iloc[:, 1], c="#1f77b4", s=40, marker="o")
        for label, (x, y) in zip(coord.index, coord.to_numpy(), strict=True):
            ax.annotate(str(label), (x, y), fontsize=9, color="#1f77b4")
    if kind in {"col", "biplot"} and "col" not in invisible:
        coord = res.col.coord.iloc[:, list(axes)]
        ax.scatter(coord.iloc[:, 0], coord.iloc[:, 1], c="darkred", s=40, marker="^")
        for label, (x, y) in zip(coord.index, coord.to_numpy(), strict=True):
            ax.annotate(str(label), (x, y), fontsize=9, color="darkred")
    _axis_decoration(ax, res, axes, title or f"CA {kind}")
    return ax


def plot_mca(
    res: Result,
    kind: str = "biplot",
    axes: tuple[int, int] = (0, 1),
    habillage: str | pd.Series | None = None,
    invisible: set[str] | None = None,
    ax: Axes | None = None,
    title: str | None = None,
) -> Axes:
    if ax is None:
        import matplotlib.pyplot as plt
        _, ax = plt.subplots(figsize=(7, 6))
    invisible = invisible or set()
    if kind in {"ind", "biplot"} and "ind" not in invisible and res.ind is not None:
        coord = res.ind.coord.iloc[:, list(axes)]
        colors = _resolve_colors(coord.shape[0], habillage, res)
        ax.scatter(coord.iloc[:, 0], coord.iloc[:, 1], c=colors, s=15, alpha=0.6)
    if kind in {"var", "biplot"} and "var" not in invisible and res.var is not None:
        coord = res.var.coord.iloc[:, list(axes)]
        ax.scatter(coord.iloc[:, 0], coord.iloc[:, 1], c="darkred", s=40, marker="s")
        for label, (x, y) in zip(coord.index, coord.to_numpy(), strict=True):
            ax.annotate(str(label), (x, y), fontsize=8, color="darkred")
    _axis_decoration(ax, res, axes, title or f"MCA {kind}")
    return ax


# -- HCPC -------------------------------------------------------------------

def plot_hcpc(
    res: HCPCResult,
    kind: str = "dendrogram",
    axes: tuple[int, int] = (0, 1),
    ax: Axes | None = None,
    title: str | None = None,
) -> Axes:
    if ax is None:
        import matplotlib.pyplot as plt
        _, ax = plt.subplots(figsize=(8, 5))
    if kind == "dendrogram":
        Z = res.call["t"]["linkage"]
        dendrogram(Z, ax=ax, color_threshold=None)
        ax.set_title(title or "HCPC dendrogram")
        return ax
    if kind == "factor_map":
        df = res.data_clust
        coord = df.iloc[:, list(axes)]
        clusters = df["clust"].to_numpy()
        for ci, c in enumerate(sorted(np.unique(clusters))):
            mask = clusters == c
            ax.scatter(coord.iloc[mask, 0], coord.iloc[mask, 1],
                       c=DEFAULT_PALETTE[ci % len(DEFAULT_PALETTE)], label=f"cluster {c}", s=30,
                       edgecolor="white", linewidth=0.5)
        ax.legend(loc="best", fontsize=8)
        ax.set_xlabel(coord.columns[0])
        ax.set_ylabel(coord.columns[1])
        ax.set_title(title or "HCPC factor map")
        ax.axhline(0, color="lightgray", lw=0.5)
        ax.axvline(0, color="lightgray", lw=0.5)
        return ax
    raise ValueError(f"unsupported HCPC kind: {kind!r}")


# -- shared -----------------------------------------------------------------

def plot_scree(res: Result, ax: Axes | None = None, title: str | None = None) -> Axes:
    if ax is None:
        import matplotlib.pyplot as plt
        _, ax = plt.subplots(figsize=(7, 4))
    pct = res.eig["percentage of variance"].to_numpy()
    ax.bar(np.arange(1, len(pct) + 1), pct, color="#1f77b4")
    ax.set_xlabel("Dimensions")
    ax.set_ylabel("Percentage of variance")
    ax.set_title(title or "Scree plot")
    return ax


def plot_contrib(res: Result, axis: int = 0, ax: Axes | None = None, title: str | None = None) -> Axes:
    if ax is None:
        import matplotlib.pyplot as plt
        _, ax = plt.subplots(figsize=(7, 4))
    block = res.var if res.var is not None else res.col
    contrib = block.contrib.iloc[:, axis].sort_values(ascending=False)
    ax.bar(range(len(contrib)), contrib.to_numpy(), color="#1f77b4")
    ax.set_xticks(range(len(contrib)))
    ax.set_xticklabels(list(contrib.index), rotation=45, ha="right")
    ax.set_ylabel("Contribution (%)")
    ax.set_title(title or f"Variable contributions to Dim.{axis + 1}")
    return ax


def _resolve_colors(n: int, habillage, res: Result) -> list[str]:
    if habillage is None:
        return ["#1f77b4"] * n
    if isinstance(habillage, str):
        groups = res.call.get("quali_sup_frame")
        if groups is None or habillage not in groups.columns:
            return ["#1f77b4"] * n
        groups = groups[habillage].astype("category")
    else:
        groups = pd.Series(habillage).astype("category")
    levels = list(groups.cat.categories)
    palette = {lvl: DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)] for i, lvl in enumerate(levels)}
    return [palette[lvl] for lvl in groups]


def _draw_confidence_ellipses(
    ax: Axes,
    coord: pd.DataFrame,
    habillage,
    res: Result,
    level: float,
    colors: list[str],
) -> None:
    if isinstance(habillage, str):
        groups = res.call.get("quali_sup_frame")
        if groups is None or habillage not in groups.columns:
            return
        groups = groups[habillage].astype("category")
    else:
        groups = pd.Series(habillage).astype("category")
    # Use the R-faithful coord.ellipse parametrization (shared with the plotly
    # backend) so our ellipses are vertex-identical to FactoMineR's, not the
    # eigenvector form a matplotlib Ellipse patch would draw.
    ellipses = coord_ellipse(coord.to_numpy(), groups, axes=(0, 1), level=level)
    codes = groups.cat.codes.to_numpy()
    for i, lvl in enumerate(groups.cat.categories):
        mask = codes == i
        if mask.sum() < 3:
            continue
        pts = ellipses[str(lvl)]
        color = colors[int(np.argmax(mask))] if colors else "gray"
        ax.plot(pts[:, 0], pts[:, 1], color=color, lw=1.2, alpha=0.7)


def _axis_decoration(ax: Axes, res: Result, axes: tuple[int, int], title: str) -> None:
    eig = res.eig.iloc[:, 1].to_numpy()  # percentage of variance
    ax.axhline(0, color="lightgray", lw=0.5)
    ax.axvline(0, color="lightgray", lw=0.5)
    ax.set_xlabel(f"Dim.{axes[0] + 1} ({eig[axes[0]]:.2f}%)")
    ax.set_ylabel(f"Dim.{axes[1] + 1} ({eig[axes[1]]:.2f}%)")
    ax.set_title(title)
