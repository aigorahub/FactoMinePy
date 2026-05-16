# factominer

A Python port of the R package
[FactoMineR](https://cran.r-project.org/package=FactoMineR), built from
primitives (NumPy/SciPy/Pandas) and validated numerically against
R FactoMineR via a checked-in fixture harness.

```{toctree}
:maxdepth: 2
:caption: Documentation

migrating-from-r
api/pca
api/ca
api/mca
api/hcpc
api/desc
api/plot
api/datasets
```

```{toctree}
:maxdepth: 1
:caption: Examples

examples/pca_decathlon
examples/ca_children
examples/mca_tea
examples/hcpc_decathlon
```

## Status

| Method | Live | R-parity |
| --- | --- | --- |
| PCA | ✅ | eigvals 5e-11, coords 5e-12 |
| CA | ✅ | eigvals 4e-13, coords 5e-12 |
| MCA | ✅ | eigvals 4e-12 |
| HCPC | ✅ | ARI = 1.0 |
| dimdesc | ✅ | correlations 1e-6 |
| catdes | ✅ | structural |
| condes | ✅ | correlations 1e-6 |
| Plotting (matplotlib) | ✅ | structural |
| FAMD, MFA, HMFA, DMFA, GPA | 🚧 stub | Round 2 |
| Plotly backend | 🚧 stub | Round 2 |

## Install

```bash
pip install factominer
```

## Quickstart

```python
from factominer import PCA, HCPC, dimdesc
from factominer.datasets import load_decathlon

decathlon = load_decathlon()
res = PCA(decathlon, scale_unit=True, ncp=5,
          quanti_sup=["Rank", "Points"],
          quali_sup=["Competition"])

print(res.summary())
clust = HCPC(res, nb_clust=3)
desc = dimdesc(res, axes=[0, 1])
```
