"""Plotly backend reproducing FactoMineR's ``plot.*`` family.

Mirrors the public surface of :mod:`factominer.plot.matplotlib_backend` but
returns ``plotly.graph_objects.Figure`` objects instead of matplotlib Axes.
Both backends draw from the same backend-agnostic geometry in
:mod:`factominer.plot._data` (the color palette and the R-faithful
``coord_ellipse``), so a figure rendered by either backend places points,
arrows, and ellipses identically.

``plotly`` is an optional dependency (``pip install 'factominer[plotly]'``);
importing this module without plotly raises a clear ``ImportError``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .._result import Result
from ..hcpc import HCPCResult
from ._data import DEFAULT_PALETTE, coord_ellipse, resolve_colors

try:
    import plotly.graph_objects as go
except ModuleNotFoundError as exc:  # pragma: no cover - exercised only without the extra
    raise ImportError(
        "the plotly backend requires plotly; install it with "
        "`pip install 'factominer[plotly]'`"
    ) from exc


def _axis_titles(res: Result, axes: tuple[int, int]) -> tuple[str, str]:
    pct = res.eig.iloc[:, 1].to_numpy()  # percentage of variance
    return (
        f"Dim.{axes[0] + 1} ({pct[axes[0]]:.2f}%)",
        f"Dim.{axes[1] + 1} ({pct[axes[1]]:.2f}%)",
    )


def _base_layout(res: Result, axes: tuple[int, int], title: str, equal: bool = False) -> go.Layout:
    xlab, ylab = _axis_titles(res, axes)
    layout = go.Layout(
        title=title,
        xaxis=dict(title=xlab, zeroline=True, zerolinecolor="lightgray"),
        yaxis=dict(title=ylab, zeroline=True, zerolinecolor="lightgray"),
        showlegend=True,
        template="simple_white",
    )
    if equal:
        layout.yaxis.scaleanchor = "x"
        layout.yaxis.scaleratio = 1
    return layout


def plot_plotly(  # noqa: N802 — mirrors the matplotlib dispatcher
    res: Result | HCPCResult,
    choix: str = "ind",
    axes: tuple[int, int] = (0, 1),
    habillage: str | pd.Series | None = None,
    invisible=None,
    title: str | None = None,
    ellipse: bool = False,
    ellipse_level: float = 0.95,
) -> go.Figure:
    """High-level plotly entry point matching the matplotlib ``plot()`` dispatcher."""
    invisible = set(invisible or [])
    if isinstance(res, HCPCResult):
        if choix == "factor_map":
            return plotly_hcpc_factor_map(res, axes=axes, title=title)
        if choix == "dendrogram":
            return plotly_hcpc_dendrogram(res, title=title)
        raise ValueError(f"unsupported choix for HCPC: {choix!r}")

    if choix == "scree":
        return plotly_scree(res, title=title)
    if choix == "contrib":
        return plotly_contrib(res, axis=axes[0], title=title)
    if choix == "ind":
        if res.method in {"CA", "MCA"}:
            return plotly_ca_mca(res, kind="row" if res.method == "CA" else "ind",
                                 axes=axes, habillage=habillage, invisible=invisible, title=title)
        return plotly_pca_ind(res, axes=axes, habillage=habillage, invisible=invisible,
                              ellipse=ellipse, ellipse_level=ellipse_level, title=title)
    if choix == "var":
        if res.method in {"CA", "MCA"}:
            return plotly_ca_mca(res, kind="col" if res.method == "CA" else "var",
                                 axes=axes, invisible=invisible, title=title)
        return plotly_pca_var(res, axes=axes, invisible=invisible, title=title)
    if choix == "biplot":
        if res.method == "PCA":
            return plotly_pca_biplot(res, axes=axes, habillage=habillage, title=title)
        if res.method in {"CA", "MCA"}:
            return plotly_ca_mca(res, kind="biplot", axes=axes, habillage=habillage,
                                 invisible=invisible, title=title)
    raise ValueError(f"unsupported choix: {choix!r}")


def plotly_pca_ind(
    res: Result,
    axes: tuple[int, int] = (0, 1),
    habillage=None,
    invisible=None,
    ellipse: bool = False,
    ellipse_level: float = 0.95,
    title: str | None = None,
) -> go.Figure:
    invisible = invisible or set()
    coord = res.ind.coord.iloc[:, list(axes)]
    fig = go.Figure(layout=_base_layout(res, axes, title or "Individuals factor map (PCA)"))
    if "ind" not in invisible:
        colors = resolve_colors(coord.shape[0], habillage,
                                res.call.get("quali_sup_frame") if isinstance(habillage, str) else None)
        fig.add_trace(go.Scatter(
            x=coord.iloc[:, 0], y=coord.iloc[:, 1], mode="markers+text",
            text=[str(i) for i in coord.index], textposition="top center",
            marker=dict(color=colors, size=8), name="individuals",
        ))
    if ellipse and habillage is not None:
        groups = (res.call.get("quali_sup_frame")[habillage] if isinstance(habillage, str)
                  else pd.Series(list(habillage)))
        groups = groups.astype("category")
        ell = coord_ellipse(coord.to_numpy(), groups, axes=(0, 1), level=ellipse_level)
        codes = groups.cat.codes.to_numpy()
        for i, lvl in enumerate(groups.cat.categories):
            if (codes == i).sum() < 3:
                continue
            pts = ell[str(lvl)]
            fig.add_trace(go.Scatter(
                x=pts[:, 0], y=pts[:, 1], mode="lines",
                line=dict(color=DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)], width=1.5),
                name=f"ellipse: {lvl}",
            ))
    ind_sup = getattr(res, "ind_sup", None)
    if "ind.sup" not in invisible and ind_sup is not None:
        s = ind_sup.coord.iloc[:, list(axes)]
        fig.add_trace(go.Scatter(x=s.iloc[:, 0], y=s.iloc[:, 1], mode="markers+text",
                                 text=[str(i) for i in s.index], textposition="top center",
                                 marker=dict(symbol="triangle-up", color="dimgray", size=9),
                                 name="ind.sup"))
    quali_sup = getattr(res, "quali_sup", None)
    if "quali.sup" not in invisible and quali_sup is not None:
        q = quali_sup.coord.iloc[:, list(axes)]
        fig.add_trace(go.Scatter(x=q.iloc[:, 0], y=q.iloc[:, 1], mode="markers+text",
                                 text=[str(i) for i in q.index], textposition="top center",
                                 marker=dict(symbol="square", color="darkred", size=10),
                                 name="quali.sup"))
    return fig


def plotly_pca_var(res: Result, axes=(0, 1), invisible=None, title=None) -> go.Figure:
    invisible = invisible or set()
    fig = go.Figure(layout=_base_layout(res, axes, title or "Variables factor map (PCA)", equal=True))
    theta = np.linspace(0, 2 * np.pi, 256)
    fig.add_trace(go.Scatter(x=np.cos(theta), y=np.sin(theta), mode="lines",
                             line=dict(color="lightgray"), name="circle", showlegend=False))
    var_block = res.var if getattr(res, "var", None) is not None else getattr(res, "quanti_var", None)
    if var_block is None:
        raise ValueError(f"{res.method} has no variable block to plot for choix='var'")
    if "var" not in invisible:
        _add_arrows(fig, var_block.coord.iloc[:, list(axes)], "#1f77b4", "variables")
    quanti_sup = getattr(res, "quanti_sup", None)
    if "quanti.sup" not in invisible and quanti_sup is not None:
        _add_arrows(fig, quanti_sup.coord.iloc[:, list(axes)], "darkgreen", "quanti.sup", dash="dash")
    fig.update_xaxes(range=[-1.1, 1.1])
    fig.update_yaxes(range=[-1.1, 1.1])
    return fig


def plotly_pca_biplot(res: Result, axes=(0, 1), habillage=None, title=None) -> go.Figure:
    coord = res.ind.coord.iloc[:, list(axes)]
    fig = go.Figure(layout=_base_layout(res, axes, title or "PCA biplot"))
    colors = resolve_colors(coord.shape[0], habillage,
                            res.call.get("quali_sup_frame") if isinstance(habillage, str) else None)
    fig.add_trace(go.Scatter(x=coord.iloc[:, 0], y=coord.iloc[:, 1], mode="markers",
                             marker=dict(color=colors, size=7), name="individuals"))
    var = res.var.coord.iloc[:, list(axes)].to_numpy()
    scale = float(np.max(np.abs(coord.to_numpy()))) / max(1e-12, float(np.max(np.abs(var))))
    scaled = pd.DataFrame(var * scale, index=res.var.coord.index)
    _add_arrows(fig, scaled, "darkred", "variables")
    return fig


def plotly_ca_mca(res: Result, kind: str, axes=(0, 1), habillage=None, invisible=None, title=None) -> go.Figure:
    invisible = invisible or set()
    fig = go.Figure(layout=_base_layout(res, axes, title or f"{res.method} factor map"))
    if res.method == "CA":
        if kind in {"row", "biplot"} and res.row is not None:
            r = res.row.coord.iloc[:, list(axes)]
            fig.add_trace(go.Scatter(x=r.iloc[:, 0], y=r.iloc[:, 1], mode="markers+text",
                                     text=[str(i) for i in r.index], textposition="top center",
                                     marker=dict(color="#1f77b4", size=8), name="rows"))
        if kind in {"col", "biplot"} and res.col is not None:
            c = res.col.coord.iloc[:, list(axes)]
            fig.add_trace(go.Scatter(x=c.iloc[:, 0], y=c.iloc[:, 1], mode="markers+text",
                                     text=[str(i) for i in c.index], textposition="top center",
                                     marker=dict(symbol="triangle-up", color="darkred", size=9), name="columns"))
    else:  # MCA
        if kind in {"ind", "biplot"} and res.ind is not None:
            ind = res.ind.coord.iloc[:, list(axes)]
            colors = resolve_colors(ind.shape[0], habillage,
                                    res.call.get("quali_sup_frame") if isinstance(habillage, str) else None)
            fig.add_trace(go.Scatter(x=ind.iloc[:, 0], y=ind.iloc[:, 1], mode="markers",
                                     marker=dict(color=colors, size=5, opacity=0.5), name="individuals"))
        if kind in {"var", "biplot"} and res.var is not None:
            v = res.var.coord.iloc[:, list(axes)]
            fig.add_trace(go.Scatter(x=v.iloc[:, 0], y=v.iloc[:, 1], mode="markers+text",
                                     text=[str(i) for i in v.index], textposition="top center",
                                     marker=dict(symbol="square", color="darkred", size=8), name="categories"))
    return fig


def plotly_scree(res: Result, title=None) -> go.Figure:
    pct = res.eig.iloc[:, 1].to_numpy()
    dims = np.arange(1, len(pct) + 1)
    fig = go.Figure(
        data=[go.Bar(x=dims, y=pct, marker_color="#1f77b4")],
        layout=go.Layout(title=title or "Scree plot", template="simple_white",
                         xaxis=dict(title="Dimension"), yaxis=dict(title="% of variance")),
    )
    return fig


def plotly_contrib(res: Result, axis: int = 0, title=None) -> go.Figure:
    block = res.var if res.var is not None else res.col
    contrib = block.contrib.iloc[:, axis].sort_values(ascending=False)
    fig = go.Figure(
        data=[go.Bar(x=[str(i) for i in contrib.index], y=contrib.to_numpy(), marker_color="#1f77b4")],
        layout=go.Layout(title=title or f"Contributions to Dim.{axis + 1}", template="simple_white",
                         xaxis=dict(title="", tickangle=-45), yaxis=dict(title="contribution (%)")),
    )
    return fig


def plotly_hcpc_factor_map(res: HCPCResult, axes=(0, 1), title=None) -> go.Figure:
    data = res.data_clust
    dim_cols = [c for c in data.columns if c != "clust"]
    xcol, ycol = dim_cols[axes[0]], dim_cols[axes[1]]
    fig = go.Figure(layout=go.Layout(title=title or "HCPC factor map", template="simple_white",
                                     xaxis=dict(title=xcol, zeroline=True),
                                     yaxis=dict(title=ycol, zeroline=True)))
    clusters = sorted(data["clust"].unique(), key=lambda v: int(v))
    for i, cl in enumerate(clusters):
        sub = data[data["clust"] == cl]
        fig.add_trace(go.Scatter(x=sub[xcol], y=sub[ycol], mode="markers+text",
                                 text=[str(j) for j in sub.index], textposition="top center",
                                 marker=dict(color=DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)], size=8),
                                 name=f"cluster {cl}"))
    return fig


def plotly_hcpc_dendrogram(res: HCPCResult, title=None) -> go.Figure:
    from scipy.cluster.hierarchy import dendrogram
    Z = res.call["t"]["linkage"]
    dd = dendrogram(Z, no_plot=True)
    fig = go.Figure(layout=go.Layout(title=title or "HCPC dendrogram", template="simple_white",
                                     xaxis=dict(title="", showticklabels=False),
                                     yaxis=dict(title="height")))
    for xs, ys in zip(dd["icoord"], dd["dcoord"], strict=True):
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#1f77b4", width=1),
                                 showlegend=False, hoverinfo="skip"))
    return fig


def _add_arrows(fig: go.Figure, coord: pd.DataFrame, color: str, name: str, dash: str | None = None) -> None:
    """Draw origin→point arrows (as line segments + a labeled marker at the tip)."""
    arr = coord.to_numpy()
    xs, ys = [], []
    for x, y in arr:
        xs += [0.0, x, None]
        ys += [0.0, y, None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines",
                             line=dict(color=color, width=1.2, dash=dash), name=name))
    fig.add_trace(go.Scatter(x=arr[:, 0], y=arr[:, 1], mode="text",
                             text=[str(i) for i in coord.index], textposition="top center",
                             textfont=dict(color=color), showlegend=False))
