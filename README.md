# FactoMinePy

[![CI](https://github.com/aigorahub/FactoMinePy/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/aigorahub/FactoMinePy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-alpha-orange)](#status)

> ⚠️ **Experimental — use with caution.** This is an independent Python port of the R package [FactoMineR](https://cran.r-project.org/package=FactoMineR). It is **not** affiliated with or endorsed by the authors of FactoMineR. The port is in early development; APIs may change, edge cases may differ from R, and several FactoMineR methods are not yet implemented (see status table below). For production work or published research, treat results as preliminary and cross-check against the original R package.

A from-primitives reimplementation in pure NumPy/SciPy/Pandas of the R package [FactoMineR](https://cran.r-project.org/package=FactoMineR) for multivariate exploratory data analysis (PCA, CA, MCA, HCPC, dimdesc/catdes/condes).

This package is **not** a wrapper around R; every method is reimplemented from the published FactoMineR documentation and R source, then validated numerically against R FactoMineR (currently 2.14 on CRAN) via a checked-in fixture harness. R FactoMineR remains the canonical reference implementation; this port aims for byte-identical fixture output and column-by-column schema parity, but is not a drop-in replacement.

## Status

**Early-alpha.** The supported-methods table is the source of truth for what works.

| FactoMineR method | Python equivalent | Live | R-parity verified | Notes |
| --- | --- | --- | --- | --- |
| `PCA` | `factominer.PCA` | ✅ | ✅ | active + supplementary individuals, quanti.sup, quali.sup |
| `CA` | `factominer.CA` | ✅ | ✅ | symmetric biplot, supplementary rows/columns |
| `MCA` | `factominer.MCA` | ✅ | ✅ | indicator matrix; Burt option |
| `HCPC` | `factominer.HCPC` | ✅ | ✅ | hierarchical clustering on PCA/CA/MCA, k-means consolidation |
| `dimdesc` | `factominer.dimdesc` | ✅ | ✅ | quantitative + categorical description per axis |
| `catdes` | `factominer.catdes` | ✅ | ✅ | `Cla/Mod`, `Mod/Cla`, `Global`, hypergeometric v-test; `quanti_var` Eta²; per-level `quanti` with `sd in category` / `Overall sd` / `n` |
| `condes` | `factominer.condes` | ✅ | ✅ | correlation tests for a continuous target |
| `plot.PCA / .CA / .MCA / .HCPC` | `factominer.plot.plot()` | ✅ | structural + ellipse | matplotlib backend; factor maps, biplot, scree, contributions, dendrogram, habillage. Confidence/concentration ellipses (`coord.ellipse`) are vertex-parity-verified against R |
| `FAMD` | `factominer.FAMD` | ✅ | ✅ | mixed quantitative + qualitative data; active variables (supplementary vars not yet supported) |
| `MFA` | `factominer.MFA` | 🚧 stub | — | Round 2 |
| `HMFA` | `factominer.HMFA` | 🚧 stub | — | Round 2 |
| `DMFA` | `factominer.DMFA` | 🚧 stub | — | Round 2 |
| `GPA` | `factominer.GPA` | 🚧 stub | — | Round 2 |
| Plotly backend | `factominer.plot.plotly_*` | 🚧 stub | — | Round 2 |

Methods marked 🚧 are importable but raise `NotImplementedError("deferred — see docs/plans/factominer-python-port.md §2")` when called. This is by design so downstream code can `from factominer import HMFA` without an `ImportError`.

## Install

```bash
pip install factominer
# matplotlib backend ships by default; for the optional plotly backend:
pip install 'factominer[plotly]'
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
print(res.eig)             # eigenvalue table (DataFrame)
print(res.ind.coord)       # individual coordinates
print(res.var.contrib)     # variable contributions

# Describe each axis
desc = dimdesc(res, axes=[0, 1])
print(desc[0]["quanti"])

# Cluster on the principal components
clust = HCPC(res, nb_clust=3)
print(clust.data_clust.head())

# Plot
import matplotlib.pyplot as plt
from factominer.plot import plot
fig, ax = plt.subplots(1, 2, figsize=(12, 5))
plot(res, choix="ind", habillage="Competition", ax=ax[0])
plot(res, choix="var", ax=ax[1])
plt.show()
```

## Migrating from R

See [docs/migrating-from-r.md](docs/migrating-from-r.md) for a side-by-side cheat sheet (R call → Python call → result attribute mapping → semantic differences).

The most important semantic differences:

1. **Argument names use snake_case.** `scale.unit=TRUE` → `scale_unit=True`, `quanti.sup=11:12` → `quanti_sup=[10, 11]` (and column names like `"Rank"` work too).
2. **Indices are 0-based.** `ind.sup=1:3` (R) → `ind_sup=[0, 1, 2]` (Python).
3. **Sign convention.** SVD is sign-ambiguous; we apply a deterministic rule (first absolute-max coordinate of each axis is positive). Coordinates may differ from R by a sign; the *interpretation* (clusters, distances, contributions) is identical. See `factominer._sign`.
4. **Result objects.** `res$eig` (R) → `res.eig` (Python). `res$var$coord` → `res.var.coord`. All result tables are `pandas.DataFrame`.
5. **Plotting is explicit.** `graph=TRUE` does not exist; you call `factominer.plot.plot(res, ...)` yourself. No magic on `print(res)`.

## Numerical fidelity

For every live method, the package ships parity tests that assert column-by-column equivalence against R FactoMineR 2.14 (current CRAN) within tight tolerances:

- Eigenvalues to **1e-10** absolute
- Coordinates / cos² / correlations / eta² to **1e-9** after sign alignment
- Contributions to **1e-8**
- v-tests to **1e-6**
- p-values to **1e-5** relative
- HCPC partitions to ARI ≥ 0.999 (k-means consolidation can swap a couple of individuals)

Fixtures are JSON dumps of R FactoMineR results, generated by `tools/refresh_r_fixtures.R` and committed under `tests/fixtures/r_outputs/`. The Python tests load them without needing R at test time. Every fixture in the repo is byte-identical to what live R FactoMineR 2.14 emits on a Linux GitHub runner with R 4.6.0 (verified by the `rpy2-parity` CI job, which is triggerable on-demand via `workflow_dispatch` and runs on a weekly cron).

To regenerate fixtures locally (requires R + FactoMineR + jsonlite):

```bash
Rscript tools/refresh_r_fixtures.R
pytest -q
```

## Known limitations / use with caution

This port targets the most common FactoMineR API surface and is rigorously validated on the bundled datasets, but the following caveats apply:

- **Several methods are stubs.** `MFA`, `HMFA`, `DMFA`, `GPA` are importable but raise `NotImplementedError` when called.
- **FAMD covers active variables only.** Supplementary variables/individuals (`sup.var` / `ind.sup` in R) are not yet implemented; pass only active data.
- **Parity is empirical, not exhaustive.** The 100 parity tests cover the active + supplementary blocks for PCA / CA / MCA / HCPC, active-variable FAMD, and the full output schemas of dimdesc / catdes / condes on standard fixtures (`decathlon`, `children`, `tea`, `poison`). Behavior with row weights, missing values, very small samples, or `method="burt"` MCA has not been independently verified.
- **Sign of axes is arbitrary.** SVD is sign-ambiguous; we apply a deterministic rule that may give the opposite sign from R on a given axis. Distances, clusters, contributions, and cos² are sign-invariant; coordinates may need a flip to align visually with R output.
- **HCPC partitions can differ by one or two individuals.** K-means consolidation is sensitive to initialization; the adjusted Rand index against R is ≥ 0.999 on the decathlon test fixture but not exactly 1.0.
- **No plotly backend yet.** Only matplotlib is implemented; the plotly module's functions raise `NotImplementedError`.

For production analyses, journal submissions, or any use where reproducibility against R FactoMineR is load-bearing, cross-check results against the original R package.

## Datasets

Bundled datasets under `factominer.datasets`:

| Loader | Source | Use case |
| --- | --- | --- |
| `load_decathlon()` | IAAF 2004 Athens Olympic + Décastar 2004, re-derived from public results | PCA, dimdesc, HCPC |
| `load_children()` | FactoMineR's `children` (children's worries by socio-educational category) | CA |
| `load_tea()` | FactoMineR's `tea` (300-person tea-consumption survey) | MCA, catdes |
| `load_poison()` | FactoMineR's `poison` (food-poisoning outbreak survey) | FAMD, mixed quantitative + categorical |

See [factominer/datasets/data/PROVENANCE.md](factominer/datasets/data/PROVENANCE.md) for each dataset's origin and licensing notes.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup, parity-bar expectations, and the PR / issue workflow. Bug reports and feature requests are welcome — please use the issue templates so we have the reproducer / R-side context up front. For security issues, see [SECURITY.md](SECURITY.md) and email `hello@aigora.com` rather than filing a public issue.

## Citing

If you use FactoMinePy in published work, please cite both this package and the original R FactoMineR (Lê, Josse, Husson, *J. Stat. Softw.* 2008, [doi:10.18637/jss.v025.i01](https://doi.org/10.18637/jss.v025.i01)). A [CITATION.cff](CITATION.cff) is included for tools that consume it automatically.

## License

MIT for code. Bundled datasets carry their original licensing — see [factominer/datasets/data/PROVENANCE.md](factominer/datasets/data/PROVENANCE.md). The package does **not** redistribute R FactoMineR source (GPL); everything is reimplemented from the published documentation and validated against R outputs.

## Acknowledgments

- The R FactoMineR package by Sébastien Lê, Julie Josse, François Husson (and many contributors) defines the API surface this package targets.
- `factoextra` for the visualization patterns that the matplotlib backend reproduces.
- `scientisttools` and `prince` for prior Python ports that informed the API shape.
