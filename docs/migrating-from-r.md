# Migrating from R's FactoMineR

A side-by-side cheat sheet for porting code from R to Python.

## Naming

| R | Python |
| --- | --- |
| `PCA(X, scale.unit=TRUE, ncp=5, graph=FALSE)` | `PCA(X, scale_unit=True, ncp=5, graph=False)` |
| `res$eig` | `res.eig` |
| `res$var$coord` | `res.var.coord` |
| `res$ind$coord` | `res.ind.coord` |
| `res$svd$vs` | `res.svd.vs` |
| `quanti.sup = 11:12` | `quanti_sup=[10, 11]` (0-based) or `quanti_sup=["Rank", "Points"]` |
| `quali.sup = 13` | `quali_sup=[12]` or `quali_sup=["Competition"]` |
| `ind.sup = 1:3` | `ind_sup=[0, 1, 2]` |
| `row.sup`, `col.sup` (CA) | `row_sup`, `col_sup` |
| `HCPC(res, nb.clust=3)` | `HCPC(res, nb_clust=3)` |
| `dimdesc(res, axes=1:2, proba=0.05)` | `dimdesc(res, axes=[0, 1], proba=0.05)` |
| `catdes(df, num.var=12)` | `catdes(df, num_var="ColumnName")` or by 0-based index |
| `plot(res, choix="ind", habillage=13)` | `plot(res, choix="ind", habillage="Competition")` |

## Semantic differences

1. **Indices are 0-based.** R's `1:3` becomes `[0, 1, 2]`. Column-name strings are
   always accepted as well and are usually clearer.
2. **Result objects are dataclasses, not lists.** Use attribute access (`res.eig`)
   instead of R's `res$eig`. Sub-objects expose `.coord`, `.cos2`, `.contrib`,
   `.cor`, `.dist`, `.v_test`, `.eta2` as `pandas.DataFrame`s or `Series`.
3. **Sign convention.** SVD signs are not unique; we apply a deterministic rule
   (first absolute-max coordinate per axis is positive). Coordinates may differ
   from R by a sign on a per-axis basis; the *interpretation* (clusters,
   distances, contributions) is identical. Use ``factominer._sign.align_to_reference``
   when comparing numerically to R outputs.
4. **No magic plotting.** `graph=TRUE` is silently accepted for source-port ease
   but does nothing. Call `factominer.plot.plot(res, ...)` yourself.
5. **MCA category labels are namespaced.** R writes `breakfast`, `Not.breakfast`;
   we write `breakfast_breakfast`, `breakfast_Not.breakfast` so labels stay
   unique across variables.
6. **HCPC linkage uses scipy's Ward.** This matches FactoMineR's default
   `method="ward"` (Ward.D2). Cluster labels themselves are arbitrary — use the
   adjusted Rand index to compare partitions.

## Round 2 (deferred)

FAMD, MFA, HMFA, DMFA, GPA, the plotly backend, the rpy2 numerical-parity lane,
and a TestPyPI release are deferred. The stubs raise `NotImplementedError` so
callers see a clean failure rather than `ImportError`.
