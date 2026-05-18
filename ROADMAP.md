# FactoMinePy roadmap

Living document for what's done, what's queued, and roughly how it's going to
get done. The bar for every cell that ends up ✅ is the same:
**byte-identical fixtures vs R FactoMineR (current CRAN), passing
`rpy2-parity` CI, and tight column-by-column tolerances** (1e-9 to 1e-10 on
exact-match channels, 1e-6 to 1e-5 on stat-test outputs).

For status of an *individual* method, the source of truth is the table in
[README.md](README.md#status). This file is the *plan*, not the snapshot.

## Where we are (v0.1.0.dev0)

| Class | Live | Parity verified | Notes |
| --- | --- | --- | --- |
| `PCA`, `CA`, `MCA` | ✅ | ✅ | active + supplementary blocks |
| `HCPC` | ✅ | ✅ | k-means consolidation, desc.var via catdes |
| `dimdesc`, `catdes`, `condes` | ✅ | ✅ | full R 2.14 schemas (Cla/Mod, n, sd in category, etc.) |
| `plot.*` matplotlib | ✅ | structural | renders, no plot-data parity tests yet |
| `FAMD`, `MFA`, `HMFA`, `DMFA`, `GPA` | 🚧 | — | importable as `NotImplementedError` stubs |
| `plot.*` plotly | 🚧 | — | stub |

## Where we're going (v1.0)

Every cell in the table ✅, the experimental warning gone from the README,
plot-data parity tests across both backends, and a CHANGELOG that ends at
`1.0.0`.

There are two pieces of work standing between here and there:

1. **The low-risk all-green sweep.** FAMD, GPA, plotly backend, plot-data
   parity tests, README/version polish. Independent methods with single R
   source files and canonical fixtures — well-suited to a focused
   autonomous run.
2. **The MFA family.** MFA itself, then HMFA and DMFA which depend on it.
   The math is harder, the design surface bigger (group inertia
   normalization, partial factor maps, RV coefficients, mixed quanti+quali
   group types), and the R source spans multiple files. Worth a dedicated
   pass with its own context budget.

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
