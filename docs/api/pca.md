# PCA

```{eval-rst}
.. autofunction:: factominer.pca.PCA
```

## Result object

`PCA` returns a {class}`factominer.Result` with these blocks:

- `eig`: eigenvalue table (eigenvalue, percentage of variance, cumulative percentage).
- `ind`: individuals block — `coord`, `cos2`, `contrib`, `dist`.
- `var`: variables block — `coord`, `cos2`, `contrib`, `cor`.
- `ind_sup`: supplementary individuals (when `ind_sup` is set).
- `quanti_sup`: supplementary continuous variables (correlations with axes).
- `quali_sup`: supplementary categorical variables (category barycenters with
  `v_test`, `cos2`, `dist`).
- `svd`: underlying SVD — `vs`, `U`, `V`.
- `call`: dict carrying the call signature, weights, and the raw qualitative
  supplementary frame (used by `dimdesc`).

## Example

```python
from factominer import PCA
from factominer.datasets import load_decathlon

df = load_decathlon()
res = PCA(df, scale_unit=True, ncp=5,
          quanti_sup=["Rank", "Points"],
          quali_sup=["Competition"])
print(res.summary())
print(res.eig.head())
print(res.var.cor.head())
```
