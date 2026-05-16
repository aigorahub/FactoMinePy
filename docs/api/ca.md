# CA

```{eval-rst}
.. autofunction:: factominer.ca.CA
```

Returns a {class}`factominer.Result` with `row` / `col` (and optionally
`row_sup` / `col_sup`) blocks. The chi-square symmetric biplot scaling is used
by default — both rows and columns are returned in the principal coordinates of
the standardized-residual SVD.
