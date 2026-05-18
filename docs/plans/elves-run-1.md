# Elves run #1 plan — low-risk all-green sweep

**Mission:** drop every 🚧 row in the README status table except the MFA
family (MFA / HMFA / DMFA) by adding FAMD, GPA, and a plotly backend, plus
plot-data parity tests. Bump to `v0.2.0.dev0`.

**Branch convention:** one working branch `feat/elves-run-1` for the
entire run; commits accumulate on it batch by batch (per the elves skill
default). Open a single PR after Batch 0 (session setup) and use it
throughout. Review happens continuously via PR comments / bots / subagent
reviews between batches; the user merges the PR after the final batch
lands.

**Compaction-recovery anchor:** this file. If context is lost mid-run, the
"Resume here" line at the top of each batch tells you what the next
unmerged step is.

---

## Pre-flight (run once at start)

- [ ] Confirm `main` is at or past `v0.1.0.dev0` (PyPI publish done, tag
      exists, release workflow proven).
- [ ] `gh workflow run ci.yml --ref main -f publish_to=none` is a no-op —
      ignore. Workflow-dispatch on `ci.yml` for `rpy2-parity` on `main`
      should report 83 passed / 2 skipped before run starts.
- [ ] Local: `.venv/bin/pytest -q` clean.

If any of the above is red, **stop and escalate** before starting batch 1.

---

## Batch 1 — FAMD

**Resume here:** if no `feat/famd-port` branch exists, this batch hasn't
started.

### Scope

Port `FactoMineR::FAMD` (Factor Analysis of Mixed Data). R source:
[husson/FactoMineR/R/FAMD.R](https://github.com/husson/FactoMineR/blob/master/R/FAMD.R)
(~300 lines, calls into `PCA.r`).

### Deliverables

- `factominer/famd.py` implementing `FAMD(X, ncp=5, ind_sup=None,
  quanti_sup=None, quali_sup=None, ...)`.
- `tools/refresh_r_fixtures.R` extended with a `FAMD(wine)` fixture (the
  canonical FactoMineR FAMD example).
- `tests/test_famd.py` asserting every R-emitted column: `eig`, `svd$vs`,
  `ind` (coord/cos²/contrib/dist), `var` (coord/cos²/contrib),
  `quanti.var` (coord/cor/cos²/contrib), `quali.var` (coord/cos²/contrib/v.test).
- README row + `factominer/_deferred.py` stub removed.
- CHANGELOG entry.

### Acceptance criteria

- `pytest -q` green (target: 85+ passed, 2 skipped).
- `ruff check factominer tests` clean.
- `rpy2-parity` CI run on the branch: zero fixture drift, 0-byte
  `r_fixture_drift.diff`.
- Tolerances: 1e-9 on coord/cos²/cor after sign alignment, 1e-8 on
  contrib, 1e-10 on eigenvalues.

### Implementation notes

- FAMD is "PCA on `[standardized quanti | (Z - col_mean)/col_sd
  indicator]` with column weights so each variable contributes 1 unit of
  inertia". Quanti columns have weight `1`; each quali column's
  indicator block shares weight `1/n_categories`.
- Reuse `factominer._scaling.center_scale` and `factominer._svd.standard_svd`
  via the existing PCA pipeline. The cleanest implementation calls into
  `factominer.pca._fit_pca` with the constructed weights rather than
  duplicating the SVD.
- Sup variables: same patterns as PCA (project on the active axes;
  weighted barycenter for sup quali).
- R's `var$cor` for FAMD is correlation with each axis for quanti and
  eta² for quali. Match the column-naming exactly.

### Stop conditions

- If R's `var$coord` for the quali half differs in sign/scale convention
  from what the FAMD source produces directly, stop and escalate.
  Reason: same class of bug as MCA's "principal vs standard coord" trap
  from the last round.

---

## Batch 2 — GPA

**Resume here:** if `feat/famd-port` is merged and no `feat/gpa-port`
branch exists.

### Scope

Port `FactoMineR::GPA` (Generalized Procrustes Analysis). R source:
[husson/FactoMineR/R/GPA.R](https://github.com/husson/FactoMineR/blob/master/R/GPA.R)
(~150 lines).

### Deliverables

- `factominer/gpa.py` implementing iterative orthogonal Procrustes with
  scaling across K configurations.
- `tools/refresh_r_fixtures.R` extended with a `GPA` fixture on the
  `wine` dataset.
- `tests/test_gpa.py` asserting `consensus`, `Xfin` (rotated
  configurations), `RV` (RV coefficient between groups), `simi`
  (similarity matrix), and `correlation` (per-group/per-dim
  correlations).
- README row + stub removed, CHANGELOG entry.

### Acceptance

Same parity bar as Batch 1.

### Implementation notes

- Iterative algorithm: at each step, fit each configuration to the
  current consensus via orthogonal Procrustes (SVD of the cross-product),
  scale to common size, update the consensus as the mean. Converges in
  ~5–10 iterations on the wine fixture.
- The "scale" step is FactoMineR-specific: it normalizes each
  configuration's Frobenius norm rather than just rotating. Match the
  formula in `R/GPA.R` (`coef.scale` calculation).

---

## Batch 3 — plotly backend

**Resume here:** if Batches 1 and 2 are merged and the plotly module
still has `NotImplementedError` stubs.

### Scope

Implement `factominer.plot.plotly_backend` mirroring the matplotlib
backend's public surface (`plot_pca_*`, `plot_ca`, `plot_mca`,
`plot_hcpc`, `plot_scree`, biplot, factor maps, dendrogram, ellipses,
habillage).

### Deliverables

- `factominer/plot/plotly_backend.py` implementing each function.
- `factominer/plot/__init__.py` dispatcher chooses backend by `backend=`
  kwarg or PLOTLY env var.
- `factominer[plotly]` extra already declared in `pyproject.toml`;
  confirm install path works.
- `tests/test_plots.py` extended with structural tests for the plotly
  backend (figure object type, expected number of traces, expected
  layout title).
- One example notebook re-rendered with the plotly backend to
  demonstrate `docs/examples/`.
- README row updated to ✅; CHANGELOG entry.

### Acceptance

- `pytest -q` green.
- Plotly tests assert structure only (trace count, trace types,
  hover-text content). No numerical parity expected because
  matplotlib's coord output is already numerically validated.

### Stop conditions

- If `pyproject.toml`'s `plotly` extra is missing required deps for any
  function (e.g., kaleido for static image export), stop and add them in
  a separate prep commit before continuing.

---

## Batch 4 — plot-data parity tests

**Resume here:** if Batches 1–3 are merged and `tests/test_plot_parity.py`
doesn't exist.

### Scope

The matplotlib backend currently has "structural" parity only — the
plots render but we never assert their underlying data matches R's
`plot.PCA` output. This batch adds a tests layer that:

1. Extracts the data each plot would draw (x/y coords, label list,
   color groups, ellipse parameters) without actually rendering.
2. Compares those extracts to R `plot.*` data via fixtures.

### Deliverables

- `factominer/plot/_data.py` exposing pure-data extractors:
  `plot_data_pca_ind`, `plot_data_pca_var`, `plot_data_ca`,
  `plot_data_mca`, `plot_data_hcpc`. Each returns a dict of NumPy
  arrays / pandas DataFrames.
- The existing matplotlib functions in `matplotlib_backend.py` refactor
  to consume `plot_data_*` output (so the plotly backend can reuse it
  unchanged).
- `tools/refresh_r_fixtures.R` extended with a fixture that captures
  R's `plot.PCA(res, choix="ind")$data` etc.
- `tests/test_plot_parity.py` asserting each field matches.

### Acceptance

- The matplotlib backend produces identical figures before/after the
  refactor (visual comparison on the example notebook; pytest passes).
- Plot-data fixtures match R's output at 1e-9 tolerance.

### Stop conditions

- R FactoMineR's plot functions don't always expose their `$data`
  internals cleanly. If extracting the data from R requires
  reverse-engineering the plot source, stop after PCA + CA — MCA and
  HCPC plots can stay at structural parity for now.

---

## Batch 5 — polish + version bump

**Resume here:** if Batches 1–4 are merged.

### Scope

- Update README status table: every cell ✅ except MFA family rows.
- Rewrite the "Experimental — use with caution" callout to a milder
  "pre-1.0, MFA family still pending" note.
- Bump `pyproject.toml` version `0.1.0.dev0` → `0.2.0.dev0`.
- Update CHANGELOG with the four batches' worth of work, tag the
  Unreleased section as `[0.2.0.dev0] — <date>`.
- Tag `v0.2.0.dev0`. The release workflow auto-publishes to PyPI.

### Acceptance

- `git tag v0.2.0.dev0` push triggers the `release.yml` workflow.
- PyPI shows `factominer 0.2.0.dev0` available.
- The new tag has an attached GitHub Release with the dist artifacts.

---

## Stop / escalation conditions (global)

Halt the run and write a status note before continuing if **any** of
these happen mid-batch:

1. **R FactoMineR's CRAN version moves**. Re-baseline fixtures, then
   decide whether to continue.
2. **A previously-✅ row regresses** in `rpy2-parity`. Land a fix in a
   separate PR before continuing the current batch.
3. **A formula in R FactoMineR's source contains an undocumented
   convention** (e.g., MCA's standard-vs-principal-coord trap from the
   last round). Stop, write the convention into the batch's notes, and
   ask for a human read before committing the fix.
4. **A batch's parity is achievable only by loosening tolerances below
   the bar in ROADMAP.md.** Stop. Tolerance-loosening is a design
   decision, not an implementation tactic.

## Total scope

- 5 batches → 5 PRs, ~1 day of focused work each. Realistic overnight
  run target: Batches 1 and 2 in the first session; 3, 4, 5 in a
  second session if needed. (Plotly and plot-data parity tests can
  parallelize against the FAMD/GPA work if the run has the budget for
  multiple branches in flight.)
