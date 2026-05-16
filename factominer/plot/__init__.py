"""Plotting utilities for factominer results (matplotlib backend by default).

Use::

    from factominer.plot import plot
    plot(res, choix="ind", habillage=None, axes=(0, 1))

For now only the matplotlib backend is available; the plotly stubs raise
``NotImplementedError``.
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
