# FactoMinePy roadmap

Living document for what's done, what's queued, and roughly how it's going to
get done. The bar for every cell that ends up ✅ is the same:
**byte-identical fixtures vs R FactoMineR (current CRAN), passing
`rpy2-parity` CI, and tight column-by-column tolerances** (1e-9 to 1e-10 on
exact-match channels, 1e-6 to 1e-5 on stat-test outputs).

For status of an *individual* method, the source of truth is the table in
[README.md](README.md#status). This file is the *plan*, not the snapshot.

## Where we are (v0.2.0.dev0)

| Class | Live | Parity verified | Notes |
| --- | --- | --- | --- |
| `PCA`, `CA`, `MCA` | ✅ | ✅ | active + supplementary blocks (MCA sup blocks not yet asserted) |
| `FAMD` | ✅ | ✅ | active variables; sup vars pending |
| `HCPC` | ✅ | ✅ | k-means consolidation, desc.var via catdes |
| `GPA` | ✅ | ⚠️ rotation-invariant | RV/RVs/simi exact; consensus/Xfin up to rotation (R's GPA is stochastic) |
| `dimdesc`, `catdes`, `condes` | ✅ | ✅ | full R 2.14 schemas; dimdesc CA/MCA branches pending |
| `plot.*` matplotlib + plotly | ✅ | structural + ellipse | both backends on a shared `_data` layer; `coord.ellipse` vertex-exact |
| `MFA` | ✅ | ✅ | active groups (types `s`/`c`/`n`); eig/ind/quanti.var/quali.var + group Lg/RV/correlation + coord.partiel + partial.axes + inertia.ratio exact; sup groups, `f`/`m` groups pending |
| `HMFA` | ✅ | ✅ | hierarchical MFA via `H` (per-level group counts); eig/ind/quanti.var/quali.var + group.coord (per level) + canonical exact; types `s`/`c`/`n` |
| `DMFA` | ✅ | ✅ | dual MFA over a grouping factor; eig/ind/var/quanti.sup + group(coord/coord.n/cos2) + cor.dim.gr/var.partiel exact; sup qualitatives pending |

Run #1 (FAMD, GPA, plotly, plot-data/ellipse parity, v0.2.0.dev0) is complete.

## Where we're going (full parity → 1.0)

The complete closure of feature parity is planned as a single large run:
**[docs/plans/elves-run-2-full-parity.md](docs/plans/elves-run-2-full-parity.md)**
(~22 batches across 6 phases). Headline pieces:

1. **MFA family** — MFA (the keystone), then HMFA and DMFA which reuse its
   primitives. The largest remaining gap.
2. **Completeness inside shipped methods** — FAMD sup vars; MCA sup-block
   parity + Burt; GPA missing-values/unequal-width; missing-value + row-weight
   support; dimdesc CA/MCA.
3. **Auxiliary functions** — `predict.*`, `reconst`, `estim_ncp`, `descfreq`.
4. **Long tail** — `CaGalt`, the regression family (`LinearModel`/`AovSum`/
   `RegBest`/`meansComp`), `textual`, utility exports.
5. **Plotting depth** — plots for the new methods, `autoLab`, `plotellipses`,
   `ellipseCA`, partial plots.
6. **Release** — README all-✅, version cut.

Out of scope (recorded, not silently dropped): the `Rcmdr` GUI plugin,
LaTeX/`xtable` printers, ggplot-mode output (no Python ggplot2; plotly is the
analogue), pixel-exact plot images.

## Strategy: two autonomous runs

Rather than one giant elves run, we split into:

### Run #1 — "low-risk all-green sweep"

**Goal:** drop every 🚧 row except the MFA family by adding FAMD, GPA, and
plotly. Side quests: plot-data parity tests, bump to `0.2.0.dev0`, remove
"experimental" warning when the table is fully ✅ minus MFA-family.

Detailed batch plan: [docs/plans/elves-run-1.md](docs/plans/elves-run-1.md).

### Run #2 — "MFA family"

**Goal:** ship MFA, HMFA, DMFA. Scope HMFA and DMFA permissively — they
may end up as documented stubs with a clear "not on the 1.0 path" note if
the design space turns out to be too costly to navigate in a single run.

The MFA plan doc gets written *after* Run #1 lands. At that point we'll
have a fresh sense of what fixture infrastructure exists and what
primitives MFA can reuse, which will inform the batch decomposition.

## What's permanently out of scope

These are things FactoMineR ships that we don't intend to port (unless
someone shows up with a concrete use case):

- The `Rcmdr` GUI plugin.
- LaTeX `xtable`-style printer outputs.
- The `simloglim` / `simul.cov` Monte Carlo simulation helpers.
- The plot dispatcher's "interactive" mode (R's `graph=TRUE` magic on
  `print(res)`).

These are scope cuts, not failures. The Python idioms we use (explicit
`factominer.plot.plot()` calls, dataframe-shaped result objects, no
`print()` side effects) intentionally diverge from R.

## How decisions land in this doc

- A new method or scope change → pull request that edits this file and the
  README status table together.
- A parity bug discovered in a "verified" cell → CHANGELOG entry + a row
  in the README "Known limitations" section if it can't be fixed
  immediately.
- A method that moves from "live" to "verified" → status-table tick plus
  a CHANGELOG entry referencing the fixture commit.
