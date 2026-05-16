# MCA

```{eval-rst}
.. autofunction:: factominer.mca.MCA
```

Indicator-matrix MCA. Each active categorical variable contributes one
indicator block to the disjunctive matrix; the resulting analysis is run as a
CA. Supplementary quantitative variables (`quanti_sup`) and supplementary
categorical variables (`quali_sup`) are accepted but the current release
focuses on the active-only result with per-category `v_test` and per-variable
`eta2`.
