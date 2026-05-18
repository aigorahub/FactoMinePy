# Contributing to FactoMinePy

Thanks for your interest. This is an early-alpha port of the R package
[FactoMineR](https://cran.r-project.org/package=FactoMineR) to Python. Below is
how to get a local dev environment going, what the parity bar is, and how to
get a change merged.

## Quick start

```bash
git clone https://github.com/aigorahub/FactoMinePy.git
cd FactoMinePy
python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest -q
```

Python **3.10 or newer** is required; CI runs on 3.11 and local development is
exercised on 3.12.

## What this project's parity bar is

Every method in the "live" column of the README's status table is validated
against R FactoMineR (currently 2.14 on CRAN) using committed JSON fixtures.
The committed fixtures must be byte-identical to what live R FactoMineR
produces on a clean Linux runner with the current CRAN release.

When you change anything that could affect numerical output:

1. Run the full test suite locally: `.venv/bin/pytest -q`.
2. If you have R + FactoMineR installed locally, regenerate fixtures with
   `Rscript tools/refresh_r_fixtures.R` and confirm the tests still pass
   against them. If you don't have R locally, the `rpy2-parity` GitHub
   Actions workflow does the same on a runner with R 4.6 + FactoMineR 2.14
   from CRAN. Trigger it manually from the Actions tab via
   `workflow_dispatch`, or wait for the weekly cron.
3. Don't loosen tolerances to make tests pass. Investigate the divergence
   instead — the current tolerances are deliberate (1e-10 on eigenvalues,
   1e-9 on coord/cos²/cor/eta², 1e-8 on contrib, 1e-6 on v.test, 1e-5
   relative on p-values).

## Style and lint

- Source is formatted to ruff defaults; `ruff check factominer tests` must be
  clean before pushing.
- We don't enforce ruff *format* yet — match the surrounding style.
- Type annotations are encouraged but not strictly required (mypy is
  advisory in CI). New public APIs should be typed.
- Docstrings: short, in the style of the existing modules
  (`factominer/desc/catdes.py` is a good model). Reference the R FactoMineR
  source path that the implementation tracks when the behaviour is
  non-obvious.

## Where to look in the source

- `factominer/pca.py`, `ca.py`, `mca.py` — the three core dimensionality-
  reduction methods. Each one builds row + column blocks plus supplementary
  blocks and stashes the input frames in `res.call` so downstream methods
  (dimdesc / catdes / condes / HCPC) can recompute against the original
  variables.
- `factominer/desc/` — `dimdesc.py` delegates to `condes.py`; `catdes.py`
  is the heavy one (test_chi2, category with Cla/Mod/Mod/Cla/Global +
  hypergeometric, quanti.var with Eta²/P-value, per-level quanti).
- `factominer/hcpc.py` — Ward + k-means consolidation. `data_clust` holds
  the original X + `clust`, and `desc_var` delegates to `catdes`.
- `factominer/_svd.py`, `_sign.py`, `_scaling.py` — shared primitives.
- `tools/refresh_r_fixtures.R` — the single source of truth for what R
  output we compare against. Edit this script (not the JSON files
  directly) if you need a new fixture.

## Opening a pull request

1. Branch from `main`. The history is rebased-merged and reasonably linear.
2. Keep the change focused. If you're rewriting a method to fix one
   parity bug, don't also reformat the file.
3. Reference the R FactoMineR source line numbers (in
   `husson/FactoMineR/R/<file>.r`) when claiming a formula matches R.
4. Make sure the PR description has a "Test plan" checklist. The default
   PR template will populate one.
5. CI gates merge on `lint-and-test` and CodeQL. `rpy2-parity` is
   non-blocking on PRs (it's expensive and depends on R availability);
   trigger it manually if your change is numerical.

## Scope

Out of scope without discussion:

- Wholesale rewrites of the parity-test layout. The current fixture
  harness is what lets us regenerate against any CRAN FactoMineR release.
- Replacing pandas/NumPy/SciPy with another stack. The point of the port
  is *no* exotic runtime dependencies.
- A drop-in `from FactoMineR import *` Python API. We deliberately follow
  Python conventions (snake_case args, 0-based indices, pandas DataFrames
  with documented column names).

In scope and welcome:

- Implementing the deferred methods (`FAMD`, `MFA`, `HMFA`, `DMFA`,
  `GPA`). Each has a stub in `factominer/_deferred.py`.
- New parity fixtures exercising untested R FactoMineR options (row
  weights, missing values, `method="burt"` MCA, etc.).
- Plotly backend (currently stubs in `factominer/plot/`).
- Documentation fixes, example notebooks, migrating-from-R additions.

## Reporting bugs

File a GitHub issue with:

- A minimal reproducer (a script + the dataset, or one of the bundled
  loaders).
- The R FactoMineR call that produces the expected output, if you have
  one.
- The Python output you got and the R output you expected.

If your reproducer needs R to demonstrate the discrepancy, please include
the R version (`R --version | head -1`) and FactoMineR version
(`packageVersion("FactoMineR")`).
