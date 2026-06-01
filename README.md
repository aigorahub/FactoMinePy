# FactoMinePy

[![CI](https://github.com/aigorahub/FactoMinePy/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/aigorahub/FactoMinePy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-alpha-orange)](#status)

> ⚠️ **Experimental — use with caution.** This is an independent Python port of the R package [FactoMineR](https://cran.r-project.org/package=FactoMineR). It is **not** affiliated with or endorsed by the authors of FactoMineR. The port is in early development; APIs may change, edge cases may differ from R, and several FactoMineR methods are not yet implemented (see status table below). For production work or published research, treat results as preliminary and cross-check against the original R package.

A from-primitives reimplementation in pure NumPy/SciPy/Pandas of the R package [FactoMineR](https://cran.r-project.org/package=FactoMineR) for multivariate exploratory data analysis (PCA, CA, MCA, HCPC, dimdesc/catdes/condes).

This package is **not** a wrapper around R; every method is reimplemented from the published FactoMineR documentation and R source, then validated numerically against R FactoMineR (currently 2.14 on CRAN) via a checked-in fixture harness. R FactoMineR remains the canonical reference implementation; this port aims for byte-identical fixture output and column-by-column schema parity, but is not a drop-in replacement.

## Status

**Early-alpha (`0.2.0.dev0`).** Live against R FactoMineR 2.14: PCA, CA, MCA,
FAMD, MFA, HMFA, DMFA, HCPC, GPA, the `dimdesc` / `catdes` / `condes`
descriptors, and matplotlib + plotly plotting backends. PCA / CA / MCA / FAMD /
MFA / HMFA / DMFA / HCPC and the descriptors are numerically parity-verified;
GPA is rotation-invariant-verified (R's GPA is stochastic); the plotting
backends are structurally verified (plus vertex-exact ellipses). The full MFA
family (MFA, HMFA, DMFA) is now live. The supported-methods table below is the
source of truth for exactly what works and at what parity bar.

| FactoMineR method | Python equivalent | Live | R-parity verified | Notes |
| --- | --- | --- | --- | --- |
| `PCA` | `factominer.PCA` | ✅ | ✅ | active + supplementary individuals, quanti.sup, quali.sup |
| `CA` | `factominer.CA` | ✅ | ✅ | symmetric biplot, supplementary rows/columns |
| `MCA` | `factominer.MCA` | ✅ | ✅ | indicator + Burt methods (both parity-verified); active + supplementary variables (`quanti_sup` correlations, `quali_sup` category barycenters with v.test/eta²). Burt is not yet combined with `quali_sup` |
| `HCPC` | `factominer.HCPC` | ✅ | ✅ | hierarchical clustering on PCA/CA/MCA, k-means consolidation |
| `dimdesc` | `factominer.dimdesc` | ✅ | ✅ | quantitative + categorical description per axis |
| `catdes` | `factominer.catdes` | ✅ | ✅ | `Cla/Mod`, `Mod/Cla`, `Global`, hypergeometric v-test; `quanti_var` Eta²; per-level `quanti` with `sd in category` / `Overall sd` / `n` |
| `condes` | `factominer.condes` | ✅ | ✅ | correlation tests for a continuous target |
| `descfreq` | `factominer.descfreq` | ✅ | ✅ | describe the rows of a frequency table by their over/under-represented columns (hypergeometric test); the CA analogue of `catdes` |
| `predict.PCA / .MCA / .FAMD / .MFA` | `factominer.predict` | ✅ | ✅ | project new (held-out) individuals onto a fitted model — `coord`, `cos2`, `dist`. Parity-verified vs live R for all four model types |
| `reconst` | `factominer.reconst` | ✅ | ✅ | low-rank reconstruction of the original table from a fitted `PCA` or `CA` result (`reconst(res, ncp)`). MFA reconstruction (all-quanti groups only) not yet exposed |
| `estim_ncp` | `factominer.estim_ncp` | ✅ | ✅ | estimate the number of PCA dimensions by GCV or the smoothing criterion |
| `plot.PCA / .CA / .MCA / .HCPC` | `factominer.plot.plot()` | ✅ | structural + ellipse | matplotlib backend; factor maps, biplot, scree, contributions, dendrogram, habillage. Confidence/concentration ellipses (`coord.ellipse`) are vertex-parity-verified against R |
| `FAMD` | `factominer.FAMD` | ✅ | ✅ | mixed quantitative + qualitative data; active variables + supplementary variables (`sup_var`: sup-quanti correlations, sup-quali barycenters with v.test/eta², `var.coord.sup` summary). Supplementary individuals (`ind_sup`) not yet supported |
| `MFA` | `factominer.MFA` | ✅ | ✅ | Multiple Factor Analysis: groups of variables (types `s`/`c`/`n`), each normalized by its first eigenvalue. Parity-verified: `eig`, `ind` (incl. partial coords `coord.partiel`), `quanti.var`, `quali.var`, the `group` block (coord/contrib/cos2/dist2/correlation + `Lg`/`RV`), `partial.axes`, and `inertia.ratio`. Active groups, uniform row weights; supplementary groups and frequency/mixed (`f`/`m`) groups are not yet supported |
| `HMFA` | `factominer.HMFA` | ✅ | ✅ | Hierarchical MFA: nested groups via `H` (per-level group counts), each level adding a `1/λ₁` normalization. Parity-verified: `eig`, `ind`, `quanti.var`, `quali.var`, `group.coord` (one matrix per hierarchy level), and `group.canonical`. Active groups (types `s`/`c`/`n`), uniform row weights |
| `DMFA` | `factominer.DMFA` | ✅ | ✅ | Dual MFA: studies how the variable cloud varies across the levels of a grouping factor (`num_fact`). Parity-verified: `eig`, `ind`, `var`, `quanti.sup`, the `group` block (`coord`/`coord.n`/`cos2` — the `v_sᵀ Cov_j v_s / λ_s` trace), and the per-group `cor.dim.gr` / `var.partiel` diagnostics. Supplementary qualitatives not yet supported |
| `GPA` | `factominer.GPA` | ✅ | ⚠️ rotation-invariant | Generalized Procrustes Analysis, including **unequal-width** configurations. `RV` / `RVs` / `simi` and the `PANOVA` per-object/per-config sum-of-squares tables are parity-verified exactly; `consensus` / `Xfin` (and `correlations`) match R up to a global rotation/reflection (R's GPA is stochastic). Missing values not yet supported |
| `CaGalt` | `factominer.CaGalt` | ✅ | ✅ | Correspondence Analysis on Generalized Aggregated Lumped Tables: relates a frequency table `Y` to contextual covariates `X`. Parity-verified for `type="s"`/`"c"` (quantitative covariates): `eig`, `ind`, `freq`, `quanti.var` (coord/cor/cos2). `type="n"` (qualitative covariates, needs a row-weighted MCA) and the bootstrap confidence ellipses are not yet supported |
| `LinearModel` / `AovSum` | `factominer.LinearModel` / `factominer.AovSum` | ✅ | ✅ | linear model with `contr.sum` (sum-to-zero) contrasts: the Type-III/II ANOVA table (`Ftest`) and the per-level coefficient table (`Ttest`), plus `r.squared`/`sigma`/`fstatistic`/`aic`/`bic`. Stepwise `selection` (aic/bic) not yet implemented |
| `RegBest` | `factominer.RegBest` | ✅ | ✅ | best-subset linear regression: the lowest-RSS subset of each size, with selection by `"r2"` / `"Cp"` / `"adjr2"`. Predictors must be numeric |
| Plotly backend | `factominer.plot.plot(..., backend="plotly")` | ✅ | structural | mirrors the matplotlib surface (ind/var/biplot/scree/contrib, CA/MCA maps, HCPC factor map + dendrogram); shares the `_data` geometry layer. Needs `pip install 'factominer[plotly]'` |

Every analytic FactoMineR method in scope is now live and parity-verified; no methods remain stubbed. Remaining gaps are at the option level (noted per row above) rather than whole methods — see [ROADMAP.md](ROADMAP.md).

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
- Coordinates / cos² / correlations / eta² to **1e-9** after sign alignment (active blocks; supplementary blocks to **1e-7**)
- Contributions to **1e-8**
- v-tests to **1e-6**
- p-values to **1e-5** relative
- GPA: `RV` / `RVs` / `simi` to **1e-6**; `consensus` / `Xfin` matched as rotation-invariant inter-object distances
- HCPC partitions to ARI ≥ 0.999 (k-means consolidation can swap a couple of individuals)

Fixtures are JSON dumps of R FactoMineR results, generated by `tools/refresh_r_fixtures.R` and committed under `tests/fixtures/r_outputs/`. The Python tests load them without needing R at test time. Every fixture in the repo is byte-identical to what live R FactoMineR 2.14 emits on a Linux GitHub runner with R 4.6.0 (verified by the `rpy2-parity` CI job, which is triggerable on-demand via `workflow_dispatch` and runs on a weekly cron).

To regenerate fixtures locally (requires R + FactoMineR + jsonlite):

```bash
Rscript tools/refresh_r_fixtures.R
pytest -q
```

## Known limitations / use with caution

This port targets the most common FactoMineR API surface and is rigorously validated on the bundled datasets, but the following caveats apply:

- **Several methods are stubs.** `MFA`, `HMFA`, `DMFA` are importable but raise `NotImplementedError` when called.
- **FAMD covers active variables only.** Supplementary variables/individuals (`sup.var` / `ind.sup` in R) are not yet implemented; pass only active data.
- **GPA parity is rotation-invariant, and the port is deterministic.** R's GPA is stochastic (random multi-start + random rank-deficient basis completion), so its `consensus` / `Xfin` are reproducible only up to a global rotation/reflection — an inherent gauge freedom of Procrustes analysis. The port implements the deterministic single-start core; `RV` / `RVs` / `simi` (computed from the raw configurations) match R exactly, and `consensus` / `Xfin` match R's inter-object distances. Currently limited to no-missing, equal-width configurations.
- **Parity is empirical, not exhaustive.** The parity suite covers the active + supplementary blocks for PCA / CA, active blocks for MCA (its supplementary blocks are not yet asserted) and HCPC, active-variable FAMD, rotation-invariant GPA, and the full output schemas of dimdesc / catdes / condes on standard fixtures (`decathlon`, `children`, `tea`, `poison`, and a synthetic GPA set). Behavior with row weights, missing values, very small samples, or `method="burt"` MCA has not been independently verified.
- **Sign of axes is arbitrary.** SVD is sign-ambiguous; we apply a deterministic rule that may give the opposite sign from R on a given axis. Distances, clusters, contributions, and cos² are sign-invariant; coordinates may need a flip to align visually with R output.
- **HCPC partitions can differ by one or two individuals.** K-means consolidation is sensitive to initialization; the adjusted Rand index against R is ≥ 0.999 on the decathlon test fixture but not exactly 1.0.
- **Plot parity is structural, not pixel-exact.** Both backends are verified to produce the expected traces/artists and the R-faithful `coord.ellipse` geometry, but not pixel-identical images. The plotly backend mirrors the matplotlib surface and shares the same data layer.

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
