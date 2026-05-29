"""Structural tests for the plotly plotting backend.

Like test_plots.py for matplotlib, these don't check pixel output — they
verify ``plot(..., backend="plotly")`` returns a ``go.Figure`` with the
expected traces, correct axis titles, and survives every choix/method
combination. The numeric geometry (coords, ellipses) is parity-tested
elsewhere (test_pca/test_ca/test_mca/test_plot_parity); both backends draw
from the same ``factominer.plot._data`` layer.
"""

from __future__ import annotations

import pytest

from factominer import CA, HCPC, MCA, PCA
from factominer.datasets import load_children, load_decathlon, load_tea
from factominer.plot import plot

go = pytest.importorskip("plotly.graph_objects")


@pytest.fixture(scope="module")
def pca_res():
    df = load_decathlon()
    return PCA(df, ncp=5, quanti_sup=["Rank", "Points"], quali_sup=["Competition"])


@pytest.fixture(scope="module")
def ca_res():
    return CA(load_children().iloc[:14, :5], ncp=4)


@pytest.fixture(scope="module")
def mca_res():
    return MCA(load_tea().iloc[:, :5], ncp=3)


@pytest.fixture(scope="module")
def hcpc_res():
    return HCPC(PCA(load_decathlon().iloc[:, :10], ncp=5), nb_clust=3)


def _fig(*a, **k):
    f = plot(*a, backend="plotly", **k)
    assert isinstance(f, go.Figure)
    return f


def test_plotly_pca_ind(pca_res):
    f = _fig(pca_res, choix="ind")
    assert len(f.data) >= 1
    assert "Dim.1" in f.layout.xaxis.title.text
    assert "Dim.2" in f.layout.yaxis.title.text


def test_plotly_pca_ind_habillage_ellipse(pca_res):
    f = _fig(pca_res, choix="ind", habillage="Competition", ellipse=True)
    # individuals + 2 ellipse traces (Decastar, OlympicG) + quali.sup
    names = [t.name for t in f.data]
    assert any(n and n.startswith("ellipse:") for n in names)


def test_plotly_pca_var_has_circle(pca_res):
    f = _fig(pca_res, choix="var")
    # correlation circle trace present (256-point ring)
    assert any(getattr(t, "x", None) is not None and len(t.x) == 256 for t in f.data)


def test_plotly_pca_biplot(pca_res):
    f = _fig(pca_res, choix="biplot", habillage="Competition")
    assert len(f.data) >= 2  # individuals + variable arrows


def test_plotly_pca_scree(pca_res):
    f = _fig(pca_res, choix="scree")
    assert f.data[0].type == "bar"
    assert len(f.data[0].y) == pca_res.eig.shape[0]


def test_plotly_pca_contrib(pca_res):
    f = _fig(pca_res, choix="contrib")
    assert f.data[0].type == "bar"
    # bars are sorted descending
    ys = list(f.data[0].y)
    assert ys == sorted(ys, reverse=True)


def test_plotly_ca(ca_res):
    for choix in ("ind", "var", "biplot"):
        f = _fig(ca_res, choix=choix)
        assert len(f.data) >= 1


def test_plotly_mca(mca_res):
    for choix in ("ind", "var", "biplot"):
        f = _fig(mca_res, choix=choix)
        assert len(f.data) >= 1


def test_plotly_hcpc_factor_map(hcpc_res):
    f = _fig(hcpc_res, choix="factor_map")
    # one trace per cluster
    assert len(f.data) == hcpc_res.data_clust["clust"].nunique()


def test_plotly_hcpc_dendrogram(hcpc_res):
    f = _fig(hcpc_res, choix="dendrogram")
    assert len(f.data) >= 1  # dendrogram link segments


def test_plotly_unknown_backend_raises(pca_res):
    with pytest.raises(ValueError, match="unknown backend"):
        plot(pca_res, choix="ind", backend="ggplot")


def test_plotly_shares_palette():
    # both backends import the same palette source
    from factominer.plot import _data, matplotlib_backend
    assert matplotlib_backend.DEFAULT_PALETTE is _data.DEFAULT_PALETTE
