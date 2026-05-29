"""Plotting utilities for factominer results.

Use::

    from factominer.plot import plot
    plot(res, choix="ind", habillage=None, axes=(0, 1))            # matplotlib
    fig = plot(res, choix="ind", backend="plotly")                 # plotly

Two backends are available: matplotlib (default; returns an ``Axes``) and
plotly (``backend="plotly"``; returns a ``plotly.graph_objects.Figure``).
Both draw from the same backend-agnostic geometry in
``factominer.plot._data``. The plotly backend needs the optional ``plotly``
dependency (``pip install 'factominer[plotly]'``).
"""

from .matplotlib_backend import (
    plot,
    plot_ca,
    plot_hcpc,
    plot_mca,
    plot_pca_biplot,
    plot_pca_ind,
    plot_pca_var,
    plot_scree,
)

__all__ = [
    "plot",
    "plot_pca_ind",
    "plot_pca_var",
    "plot_pca_biplot",
    "plot_scree",
    "plot_ca",
    "plot_mca",
    "plot_hcpc",
]
