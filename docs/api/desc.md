# dimdesc / catdes / condes

```{eval-rst}
.. autofunction:: factominer.desc.dimdesc.dimdesc
.. autofunction:: factominer.desc.catdes.catdes
.. autofunction:: factominer.desc.condes.condes
```

## dimdesc

Describe each requested PC axis by the active and supplementary variables.
Returns a dict keyed by axis index (0-based). Each entry maps section names
(`"quanti"`, `"quali"`, `"category"`) to a sorted `DataFrame` of significant
relationships (correlations + p-values, eta² + F-tests, per-category v-tests).

## catdes

Describe a categorical target by the rest of the columns: chi-square
independence tests for categorical features, eta² + F-test for continuous
features, and per-level v-tests on each pair.

## condes

Describe a continuous target by the rest of the columns: Pearson correlation
+ Student-t p-value for continuous features, eta² + F-test for categorical
features, and per-category v-tests.
