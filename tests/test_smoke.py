"""Package-level smoke tests — every public symbol imports and runs."""

from __future__ import annotations

import pandas as pd
import pytest

import factominer
from factominer import CA, HCPC, MCA, PCA, catdes, condes, dimdesc
from factominer.datasets import load_children, load_decathlon, load_tea


def test_version_string():
    assert isinstance(factominer.__version__, str)


def test_pca_runs():
    df = load_decathlon()
    res = PCA(df, ncp=5, quanti_sup=["Rank", "Points"], quali_sup=["Competition"])
    assert res.method == "PCA"
    assert res.eig.shape[0] == 5
    assert res.ind.coord.shape == (df.shape[0], 5)
    assert "Dim.1" in res.ind.coord.columns


def test_ca_runs():
    children = load_children()
    res = CA(children.iloc[:14, :5], ncp=3)
    assert res.method == "CA"
    assert res.eig.shape[0] >= 1
    assert res.row.coord.shape[0] == 14


def test_mca_runs():
    tea = load_tea()
    res = MCA(tea.iloc[:, :5], ncp=3)
    assert res.method == "MCA"
    assert res.ind.coord.shape[0] == 300


def test_hcpc_runs_on_pca():
    df = load_decathlon().iloc[:, :10]
    res = PCA(df, ncp=5)
    clust = HCPC(res, nb_clust=3)
    assert "clust" in clust.data_clust.columns
    assert set(clust.data_clust["clust"].unique()).issubset({1, 2, 3})


def test_dimdesc_runs():
    df = load_decathlon()
    res = PCA(df, ncp=3, quanti_sup=["Rank", "Points"], quali_sup=["Competition"])
    desc = dimdesc(res, axes=[0, 1])
    assert 0 in desc and 1 in desc


def test_catdes_runs():
    tea = load_tea()
    res = catdes(tea[["Tea", "How", "where", "tearoom", "friends", "resto"]], num_var="Tea")
    assert isinstance(res, dict)


def test_condes_runs():
    df = load_decathlon()
    res = condes(df, num_var="Points")
    assert "quanti" in res or "quali" in res


@pytest.mark.parametrize("name", ["FAMD", "MFA", "HMFA", "DMFA", "GPA"])
def test_deferred_methods_raise(name):
    fn = getattr(factominer, name)
    with pytest.raises(NotImplementedError):
        fn(pd.DataFrame({"a": [1, 2, 3]}))
