"""Structural tests for the matplotlib plotting backend.

These don't check pixel-exact images (too fragile across matplotlib versions);
they check that the plot functions produce the expected number of artists,
correct axis labels, and survive both happy and edge-case inputs.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from factominer import CA, HCPC, MCA, PCA
from factominer.datasets import load_children, load_decathlon, load_tea
from factominer.plot import plot, plot_pca_biplot, plot_pca_ind, plot_pca_var, plot_scree


@pytest.fixture
def pca_res():
    df = load_decathlon()
    return PCA(df, ncp=5, quanti_sup=["Rank", "Points"], quali_sup=["Competition"])


def test_plot_pca_ind_renders(pca_res):
    fig, ax = plt.subplots()
    out = plot_pca_ind(pca_res, axes=(0, 1), ax=ax)
    assert out is ax
    assert "Dim.1" in ax.get_xlabel()
    assert "Dim.2" in ax.get_ylabel()
    plt.close(fig)


def test_plot_pca_ind_with_habillage(pca_res):
    fig, ax = plt.subplots()
    plot_pca_ind(pca_res, axes=(0, 1), habillage="Competition", ax=ax, ellipse=True)
    plt.close(fig)


def test_plot_pca_var_correlation_circle(pca_res):
    fig, ax = plt.subplots()
    plot_pca_var(pca_res, axes=(0, 1), ax=ax)
    assert ax.get_xlim() == (-1.1, 1.1)
    assert ax.get_ylim() == (-1.1, 1.1)
    plt.close(fig)


def test_plot_pca_biplot_runs(pca_res):
    fig, ax = plt.subplots()
    plot_pca_biplot(pca_res, axes=(0, 1), ax=ax)
    plt.close(fig)


def test_plot_scree_runs(pca_res):
    fig, ax = plt.subplots()
    plot_scree(pca_res, ax=ax)
    plt.close(fig)


def test_plot_dispatch_pca_ind(pca_res):
    fig, ax = plt.subplots()
    plot(pca_res, choix="ind", ax=ax)
    plt.close(fig)


def test_plot_dispatch_ca():
    ch = load_children().iloc[:14, :5]
    res = CA(ch, ncp=3)
    fig, ax = plt.subplots()
    plot(res, choix="ind", ax=ax)
    plt.close(fig)


def test_plot_dispatch_mca():
    tea = load_tea()
    res = MCA(tea.iloc[:, :8], ncp=3)
    fig, ax = plt.subplots()
    plot(res, choix="var", ax=ax)
    plt.close(fig)


def test_plot_dispatch_hcpc():
    df = load_decathlon().iloc[:, :10]
    pca = PCA(df, ncp=5)
    clust = HCPC(pca, nb_clust=3)
    fig, ax = plt.subplots()
    plot(clust, choix="dendrogram", ax=ax)
    plt.close(fig)
    fig, ax = plt.subplots()
    plot(clust, choix="factor_map", ax=ax)
    plt.close(fig)
