"""Programmatically build the example notebooks under docs/examples/.

Each notebook is created with nbformat and then executed via nbclient so that
the published docs ship pre-rendered outputs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).parent.parent
EXAMPLES_DIR = ROOT / "docs" / "examples"
EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def make_nb(cells: list[tuple[str, str]]) -> nbformat.NotebookNode:
    """``cells`` is a list of ``(kind, source)`` pairs; ``kind`` is 'md' or 'py'."""
    nb = nbformat.v4.new_notebook()
    for kind, source in cells:
        if kind == "md":
            nb.cells.append(nbformat.v4.new_markdown_cell(source))
        elif kind == "py":
            nb.cells.append(nbformat.v4.new_code_cell(source))
    nb.metadata.kernelspec = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    return nb


def execute_and_save(nb: nbformat.NotebookNode, path: Path) -> None:
    client = NotebookClient(nb, timeout=120, kernel_name="python3")
    client.execute()
    nbformat.write(nb, path)
    print(f"wrote {path}")


def pca_decathlon() -> None:
    cells = [
        ("md", "# PCA on the decathlon dataset\n\nReproduces the canonical FactoMineR PCA example."),
        ("py", """import matplotlib.pyplot as plt
from factominer import PCA, HCPC, dimdesc
from factominer.datasets import load_decathlon

df = load_decathlon()
df.head()"""),
        ("py", """res = PCA(df, scale_unit=True, ncp=5,
          quanti_sup=["Rank", "Points"],
          quali_sup=["Competition"])
print(res.summary())"""),
        ("py", """from factominer.plot import plot
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
plot(res, choix="ind", habillage="Competition", ax=axes[0])
plot(res, choix="var", ax=axes[1])
plt.tight_layout()
plt.show()"""),
        ("py", """desc = dimdesc(res, axes=[0, 1])
desc[0].get("quanti", "no quanti").head() if hasattr(desc[0].get("quanti", None), 'head') else desc[0]"""),
        ("py", """clust = HCPC(res, nb_clust=3)
fig, ax = plt.subplots(figsize=(7, 5))
plot(clust, choix="factor_map", ax=ax)
plt.show()"""),
    ]
    execute_and_save(make_nb(cells), EXAMPLES_DIR / "pca_decathlon.ipynb")


def ca_children() -> None:
    cells = [
        ("md", "# CA on the children dataset\n\nClassic correspondence analysis on a contingency table."),
        ("py", """import matplotlib.pyplot as plt
from factominer import CA
from factominer.datasets import load_children

ch = load_children()
print(ch.head())"""),
        ("py", """res = CA(ch, ncp=4, row_sup=list(range(14, 18)), col_sup=list(range(5, 8)))
print(res.eig.round(4))"""),
        ("py", """from factominer.plot import plot
fig, ax = plt.subplots(figsize=(7, 6))
plot(res, choix="biplot", ax=ax)
plt.show()"""),
    ]
    execute_and_save(make_nb(cells), EXAMPLES_DIR / "ca_children.ipynb")


def mca_tea() -> None:
    cells = [
        ("md", "# MCA on the tea dataset\n\nMultiple correspondence analysis with categorical survey data."),
        ("py", """import matplotlib.pyplot as plt
from factominer import MCA
from factominer.datasets import load_tea

tea = load_tea()
res = MCA(tea, ncp=5, quanti_sup=[18], quali_sup=list(range(19, 36)))
print(res.eig.head().round(4))"""),
        ("py", """from factominer.plot import plot
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
plot(res, choix="ind", ax=axes[0])
plot(res, choix="var", ax=axes[1])
plt.tight_layout()
plt.show()"""),
    ]
    execute_and_save(make_nb(cells), EXAMPLES_DIR / "mca_tea.ipynb")


def hcpc_decathlon() -> None:
    cells = [
        ("md", "# HCPC clustering on PCA(decathlon)\n\nHierarchical clustering on principal components, with Ward linkage and k-means consolidation."),
        ("py", """import matplotlib.pyplot as plt
from factominer import PCA, HCPC
from factominer.datasets import load_decathlon
from factominer.plot import plot

df = load_decathlon().iloc[:, :10]
pca = PCA(df, ncp=5)
clust = HCPC(pca, nb_clust=4)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
plot(clust, choix="dendrogram", ax=axes[0])
plot(clust, choix="factor_map", ax=axes[1])
plt.tight_layout()
plt.show()"""),
        ("py", """clust.data_clust["clust"].value_counts().sort_index()"""),
    ]
    execute_and_save(make_nb(cells), EXAMPLES_DIR / "hcpc_decathlon.ipynb")


def main() -> None:
    pca_decathlon()
    ca_children()
    mca_tea()
    hcpc_decathlon()


if __name__ == "__main__":
    main()
