# Notices and attributions

FactoMinePy is a from-primitives Python reimplementation of R FactoMineR. It
does **not** redistribute any R or C source code from FactoMineR. The runtime
package is MIT-licensed (see [LICENSE](LICENSE)).

## R FactoMineR

R FactoMineR is GPL-licensed and authored by:

> Sébastien Lê, Julie Josse, François Husson — *FactoMineR: An R Package for
> Multivariate Analysis* — Journal of Statistical Software 25(1), 2008 —
> doi:[10.18637/jss.v025.i01](https://doi.org/10.18637/jss.v025.i01) —
> CRAN: https://cran.r-project.org/package=FactoMineR

The Python source in this repository implements the same statistical methods
following the published documentation and the R source code at
https://github.com/husson/FactoMineR. Each implementation file references the
specific R function it tracks. The Python re-implementation is original work
and is offered under the MIT license; it does not relicense R FactoMineR.

## Bundled datasets

The CSV files under [factominer/datasets/data/](factominer/datasets/data/)
are re-extracted from the data exports shipped with R FactoMineR for the
purpose of validating numerical parity. The values themselves are facts
(athletics results, survey responses) and are not subject to copyright. The
specific tabulations distributed with R FactoMineR carry the GPL alongside
the rest of the R package; we keep these tabulations bundled solely so the
parity tests are reproducible without a working R installation.

If you need a strictly GPL-free data bundle (for example, if you are
redistributing a derivative of this package in a non-GPL-compatible
context), re-derive each dataset from its primary source as documented in
[factominer/datasets/data/PROVENANCE.md](factominer/datasets/data/PROVENANCE.md).

## Inspiration

API shape and visualization patterns were informed by:

- [`factoextra`](https://rpkgs.datanovia.com/factoextra/) — the canonical
  ggplot2 visualization companion for FactoMineR.
- [`prince`](https://github.com/MaxHalford/prince) and
  [`scientisttools`](https://pypi.org/project/scientisttools/) — earlier
  Python ports that informed the API shape (no code copied).
