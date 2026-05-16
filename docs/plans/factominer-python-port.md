# FactoMineR → Python Port — Overnight Elves Plan (Full Surface)

**Branch:** `claude/plan-factominer-python-port-NkkvY`
**Mode:** single-session unattended elves run, full FactoMineR surface
**Status:** plan only; no code yet
**Last updated:** 2026-05-16

> User decision: do the entire surface tonight, including HMFA / DMFA / GPA, full plot parity, the rpy2 R-parity lane, Sphinx site, and a TestPyPI-ready dist. Container is Ubuntu 24.04 with `apt`, so R + FactoMineR can be installed live and every method validated against R fixtures generated inside the run itself.

## 1. Mission

Land an importable, MIT-licensed Python package **`factominer`** under `factominer-py/` that is a full Python port of FactoMineR 2.14:

- **Factor methods:** `PCA`, `CA`, `MCA`, `FAMD`, `MFA`, `HMFA`, `DMFA`, `GPA`
- **Clustering:** `HCPC` over PCA/MCA/MFA results
- **Description:** `dimdesc`, `catdes`, `condes`
- **Plotting parity:** matplotlib backend reproducing `plot.PCA` / `plot.CA` / `plot.MCA` / `plot.FAMD` / `plot.MFA` / `plot.HCPC` (individuals factor map, variables factor map / correlation circle, biplot, scree, contributions bars, dendrogram, factor map colored by cluster, ellipses, habillage, invisible filtering). Plotly backend for the same plots, opt-in via extras.
- **Datasets:** decathlon, wine, tea, hobbies, children, geomorphology, milk, gironde, juice, poison, housetasks — every dataset re-derived from primary public sources with provenance recorded.
- **Validation:** R + FactoMineR installed in-container; `tools/refresh_r_fixtures.R` writes JSON ground truth per method × dataset; Python tests assert numerical parity within tight tolerance. Optional live `rpy2` lane for re-verification.
- **Docs:** Sphinx site with `migrating-from-r.md` cheat sheet and one executed notebook per method.
- **Release:** TestPyPI-ready `sdist` + `wheel` built and committed under `factominer-py/dist/`. Actual upload is blocked on a token from the user, so the run produces the artifact but does not push to TestPyPI.

The port is strictly additive: `factominer-py/` must not be imported by `ml/` or `src/`. The demo runtime path is untouched.

## 2. Risk posture for "everything tonight"

Some methods (HMFA, DMFA, GPA, some MCA edge cases) have surface that's nearly absent in `scientisttools` and has to be implemented from the FactoMineR PDF directly. Honest call:

- **First attempt is from primitives** (numpy/scipy SVD + the PDF formulas) for HMFA, DMFA, GPA.
- **If R-parity refuses to converge** (more than 30 minutes of retry on one method without crossing tolerance), ship the method with the failing fixture test marked `pytest.mark.xfail(strict=True, reason="R-parity not yet reached")` and a one-paragraph "Known limitation" entry in the method's docstring + Sphinx page. The method is still callable and returns structurally valid output; just the numerical match to R is held over.
- **Do not skip shipping any method.** Each gets a constructor function, a `Result`, a `summary()`, a `plot()`, an example notebook, and at least the structural-invariant tests green.

This is the only honest way to commit to "everything tonight" without lying about parity if a hard case fights back.

## 3. Stop gates (abort and report)

The run must stop, write its final status to `docs/elves/factominer-python-port-execution-log.md`, commit, push, and surface to the user if:

1. **Preflight fails** for any reason other than the known `scripts/check_open_ends_ui_copy.py` failure documented in the master execution log.
2. **Foundation invalid.** `scientisttools` doesn't install on Python 3.11 with pinned versions, *or* its PCA output on decathlon is structurally broken (NaNs, wrong shape, eigenvalues don't sum to trace within 1e-6).
3. **R install fails *and* R-parity fixtures from a backup source also fail.** First fallback: install R via `apt install -y r-base` and FactoMineR via `Rscript -e 'install.packages("FactoMineR", repos="https://cloud.r-project.org")'`. Second fallback: install via `conda` if available. Third fallback: degrade to structural-invariant + `scientisttools`-snapshot tests only and surface to user. Do **not** mark methods as parity-verified if R never ran.
4. **Existing repo checks regress.** `npm run lint`, `npm run typecheck`, `npm run build`, and `python3 -m compileall ml scripts` must continue to pass at every commit.
5. **Working tree drifts** outside `factominer-py/`, `docs/plans/factominer-python-port.md`, `docs/elves/factominer-python-port-*.md`, `.elves-session.json` without a written justification in the execution log.
6. **Three consecutive red batches** (not just three failures — three batches where every test attempt and every fix attempt is red).

## 4. Container prep done by Batch 0

```bash
sudo apt-get update -y
sudo apt-get install -y r-base r-base-dev libxml2-dev libcurl4-openssl-dev libssl-dev
sudo Rscript -e 'install.packages(c("FactoMineR","jsonlite"), repos="https://cloud.r-project.org")'
python3 -m venv .venv-factominer
.venv-factominer/bin/pip install -U pip wheel
.venv-factominer/bin/pip install numpy scipy pandas matplotlib plotly scientisttools pytest pytest-cov ruff mypy rpy2 sphinx myst-parser nbformat nbclient jupyter build twine
```

Cache the wheels and the R library under `.venv-factominer/` and `/usr/lib/R/site-library/` respectively. The container is ephemeral but the build is reproducible because every install is pinned in `factominer-py/requirements-dev.txt` and `tools/install-r.sh`.

## 5. Batches

Nineteen batches. Each batch ends with: commit, push to `claude/plan-factominer-python-port-NkkvY`, append a dated entry to `docs/elves/factominer-python-port-execution-log.md`. Subagent parallelism is allowed and encouraged where the plan calls it out — but the same agent runs serially across batches so the test cycle is coherent.

### Batch 0 — Preflight + container prep + fixtures-toolchain

- Run `PROFILE_NOTES_ALLOW_SLEEPING_RUNTIME=1 NEXT_TELEMETRY_DISABLED=1 bash scripts/elves-preflight.sh`. Tolerate only the known open-ends UI copy guard failure.
- Install R + FactoMineR + Python toolchain as in §4. Pin versions into `factominer-py/requirements-dev.txt` and `factominer-py/tools/install-r.sh`.
- Smoke: run `Rscript -e 'library(FactoMineR); res<-PCA(decathlon, graph=FALSE); cat(res$eig[1,1])'`. Expect a number.
- Smoke: run `python -c "import scientisttools; print(scientisttools.__version__)"`.
- Create `.elves-session.json` + `docs/elves/factominer-python-port-execution-log.md` + `docs/elves/factominer-python-port-learnings.md` (header only).
- Commit and push.

**Exit:** R FactoMineR callable, scientisttools importable, preflight survived.

### Batch 1 — Package skeleton + result contract + sign convention

- `factominer-py/pyproject.toml` (MIT, name `factominer`, version `0.1.0.dev0`, extras `dev` / `plotly` / `rpy2`).
- `factominer-py/LICENSE`, `factominer-py/factominer/__init__.py` re-exporting stubs of every public symbol.
- `factominer/_result.py`: frozen `Result` with R-mirroring attributes (`eig`, `var`, `ind`, `quanti_sup`, `quali_sup`, `ind_sup`, `quanti_var_sup`, `quali_var_sup`, `svd`, `call`). Sub-objects expose `.coord`, `.cos2`, `.contrib`, `.cor` as `pandas.DataFrame`s.
- `factominer/_sign.py`: deterministic sign convention — "first absolute-max coordinate of each column is positive". Apply uniformly across methods *and* to R fixtures during comparison.
- `factominer/_svd.py`: shared weighted SVD primitive used by every method.
- `factominer/_scaling.py`: scale.unit, row/col weights, missing-handling.
- `.github/workflows/factominer-py.yml`: ruff + mypy + pytest scoped to `factominer-py/`.
- Smoke tests for `Result` (immutability, picklability) and sign convention (idempotent, deterministic).
- Commit and push.

**Exit:** `pip install -e factominer-py/[dev]` works, smoke pytest green, CI green.

### Batch 2 — Datasets + provenance + R-fixture harness

- Bundle datasets under `factominer/datasets/data/`: decathlon, wine, tea, hobbies, children, geomorphology, milk, gironde, juice, poison, housetasks. Each re-derived from a primary public source; URLs and retrieval dates recorded in `factominer/datasets/data/PROVENANCE.md`. **Do not lift CSVs from the R package** — that would be a GPL re-distribution.
- `factominer/datasets/__init__.py` exposes `load_decathlon()`, etc.
- `factominer-py/tools/refresh_r_fixtures.R`: for each method × dataset combination, run FactoMineR with documented options and `jsonlite::write_json` the result (eigenvalues, individual + variable coords / cos² / contributions, supplementary tables, cluster assignments where relevant) into `tests/fixtures/r_outputs/<method>/<dataset>.json`.
- Run the script. Commit fixtures.
- `tests/conftest.py`: fixture loader that returns a structured object with the R results, sign-aligned to the project convention.
- Commit and push.

**Exit:** all dataset loaders importable; R fixtures generated and committed; conftest loads them.

### Batch 3 — PCA + parity

- `factominer/pca.py`: `PCA(X, scale_unit=True, ncp=5, ind_sup=None, quanti_sup=None, quali_sup=None, row_w=None, col_w=None, graph=False)`. Heavy lifting via `scientisttools` where it matches; otherwise compute directly. Always return a normalized R-shape `Result`.
- `Result.summary()` produces R-shaped printed tables.
- Tests in `tests/test_pca.py`:
  - structural invariants (eigvals sum ≈ trace, contributions sum to 100 per axis, sup-individual projection identity)
  - **R-parity** on decathlon and wine to `1e-6` after sign alignment; eigenvalues to `1e-8`
- Commit and push.

**Exit:** PCA fully parity-verified against R on two datasets.

### Batch 4 — CA + parity

- `factominer/ca.py`: same pattern. Supplementary rows/columns. Symmetric + asymmetric biplot data.
- Tests on `children` (canonical CA dataset).
- Commit and push.

### Batch 5 — MCA + parity

- `factominer/mca.py`: Burt and indicator-matrix options; supplementary quanti + quali variables; categories.
- Tests on `tea` and `hobbies`.
- Commit and push.

### Batch 6 — FAMD + parity

- `factominer/famd.py`: mixed-data PCA. Verify the FactoMineR PDF's weighting on quantitative vs qualitative blocks (the standard scaling that balances continuous and categorical inertia).
- Tests on `geomorphology` and `wine` (with synthetic categorical column appended for second case).
- Commit and push.

### Batch 7 — MFA + parity

- `factominer/mfa.py`: multi-group PCA, partial axes, supplementary groups. Group definitions via `group` and `type` like in R.
- Tests on `wine` and a small synthetic 3-group dataset.
- Commit and push.

### Batch 8 — HMFA from primitives

- `factominer/hmfa.py`: hierarchical MFA — nested groups, multi-level weighting. Implement from FactoMineR PDF formulas; `scientisttools` does not ship this. May spawn a subagent to draft a numerical-validation script while the main agent codes the method.
- Tests on `wine` with a 2-level group hierarchy. **Apply the xfail policy from §2 if R-parity refuses to converge within 30 min of retry.**
- Commit and push.

### Batch 9 — DMFA from primitives

- `factominer/dmfa.py`: dual MFA. Same approach as HMFA — direct from PDF formulas, structural invariants first, then R-parity. xfail policy applies.
- Tests on a small synthetic dataset that matches the FactoMineR PDF's worked example.
- Commit and push.

### Batch 10 — GPA from primitives

- `factominer/gpa.py`: Generalized Procrustes Analysis. SVD-based Procrustes alignment across configurations, then consensus + residual decomposition. Tests on a small synthetic multi-judge sensory dataset.
- Commit and push.

### Batch 11 — HCPC

- `factominer/hcpc.py`: `HCPC(res, nb_clust=-1, min=3, max=10, consol=True, iter_max=10, ...)`. Auto-cut on largest relative loss in within-inertia, k-means consolidation, cluster description tables.
- Operates on PCA/CA/MCA/FAMD/MFA results.
- Tests: ARI ≥ 0.999 against R on PCA(wine) and MCA(tea). Re-running with the same seed reproduces the partition exactly.
- Commit and push.

### Batch 12 — dimdesc / catdes / condes

- `factominer/desc/dimdesc.py`, `catdes.py`, `condes.py` using scipy.stats. v-test, eta², F-test, hypergeometric tail. **Verify one-sided vs two-sided conventions against the FactoMineR PDF §6.5 before coding.**
- Tests: p-values and v-test values match R within `1e-6` on decathlon / tea / wine.
- Commit and push.

### Batch 13 — Plotting matplotlib backend (Part 1: factor maps + scree + biplot)

- `factominer/plot/matplotlib_backend.py`: implement `plot(res, choix=..., habillage=..., invisible=..., axes=...)` for PCA / CA / MCA / FAMD / MFA. Reproduce R's:
  - individuals factor map (points + labels, optional `habillage` coloring, `invisible="row"/"col"/"row.sup"/"quali.sup"` filtering)
  - variables factor map (correlation circle for quantitative; arrows for variables; labels)
  - biplot (overlay)
  - scree plot
  - contributions bars (per axis)
- Snapshot tests use matplotlib's `image_comparison` with a generous tolerance (RMS < 5 over the 0-255 range). Snapshots regenerated only on demand via env var.
- Commit and push.

### Batch 14 — Plotting matplotlib backend (Part 2: HCPC + ellipses)

- HCPC: dendrogram, factor map colored by cluster, 3D view (matplotlib `Axes3D`).
- Confidence ellipses (`coord.ellipse` re-implementation): both concentration and confidence types, per-`habillage` group.
- Commit and push.

### Batch 15 — Plotly backend

- `factominer/plot/plotly_backend.py`: parity for the same plots as Batches 13/14 — interactive scatter, correlation circle, biplot, dendrogram, scree, contributions. Behind the `plotly` extra.
- Tests check figure JSON has the expected traces (no rendering needed).
- Commit and push.

### Batch 16 — Examples + Sphinx docs

- One executed notebook per live method, under `factominer-py/docs/examples/`:
  - `pca_decathlon.ipynb`, `ca_children.ipynb`, `mca_tea.ipynb`, `famd_geomorphology.ipynb`, `mfa_wine.ipynb`, `hmfa_wine.ipynb`, `dmfa_synthetic.ipynb`, `gpa_judges.ipynb`, `hcpc_wine.ipynb`, `dimdesc_decathlon.ipynb`.
- Sphinx site under `factominer-py/docs/`: `conf.py`, `index.md`, `api/<method>.md` per method, `migrating-from-r.md` cheat sheet (R call → Python call → result attribute mapping → semantic differences, especially sign convention and xfail'd parity items).
- `sphinx-build -b html docs docs/_build/html` runs clean.
- Commit and push.

### Batch 17 — `rpy2` parity lane + CI matrix

- Optional `pytest -m rpy2` lane that re-runs the parity tests live against R via `rpy2`. Skipped automatically if R or `rpy2` is absent.
- Extend the CI workflow: add a job that installs R + FactoMineR + rpy2 and runs the rpy2 lane weekly (cron) rather than per-PR.
- Commit and push.

### Batch 18 — Release-ready dist + README + closeout

- `python -m build` produces `dist/factominer-0.1.0-py3-none-any.whl` and `dist/factominer-0.1.0.tar.gz` under `factominer-py/dist/`.
- `twine check dist/*` clean.
- **Do not upload to TestPyPI** — user holds the token. Note explicitly in the README how to upload when ready.
- `factominer-py/README.md`: install, supported-methods table (✓ / xfail per method with a link to the relevant docs page), quickstart, FactoMineR → Python cheat sheet pointer, license, provenance pointer.
- Final test cycle: `cd factominer-py && pytest -q` (all green or only documented xfails red); re-run the repo's preflight to prove no regression in `ml/` or `src/`; `sphinx-build` clean; `twine check` clean.
- `docs/elves/factominer-python-port-learnings.md`: full retrospective — what surprised, every R-parity gotcha (sign flips, NA handling, MFA group-weight conventions), every place scientisttools disagreed with FactoMineR, every method that needed an xfail and why.
- Final commit, final push, write a one-paragraph completion summary at the bottom of the execution log naming the live methods, the xfail'd parity items, the deferred items (none, unless §2 fired), and the verify-by-hand steps.
- Stop. Do not open a PR — user opens it after morning review.

**Exit:** Branch is review-ready with the full FactoMineR surface live and parity-verified where R cooperated.

## 6. Estimated wall-clock budget

| Batch | Estimate |
| --- | --- |
| 0 Preflight + container prep | 30 min |
| 1 Skeleton + result contract | 60 min |
| 2 Datasets + R fixtures | 90 min |
| 3 PCA | 75 min |
| 4 CA | 45 min |
| 5 MCA | 60 min |
| 6 FAMD | 75 min |
| 7 MFA | 90 min |
| 8 HMFA | 90 min |
| 9 DMFA | 75 min |
| 10 GPA | 60 min |
| 11 HCPC | 60 min |
| 12 dimdesc / catdes / condes | 75 min |
| 13 Plotting matplotlib Part 1 | 120 min |
| 14 Plotting matplotlib Part 2 | 75 min |
| 15 Plotly backend | 60 min |
| 16 Examples + Sphinx | 120 min |
| 17 rpy2 parity lane + CI | 45 min |
| 18 Release-ready dist + closeout | 60 min |
| **Total** | **~22 h** |

If overnight is ~10–12 h, this exceeds the budget. The plan is calibrated to push hard and use the xfail policy from §2 as the pressure valve, not the goal. Realistic outcome at morning:

- **Highly likely live and R-parity-verified:** PCA, CA, MCA, FAMD, MFA, HCPC, dimdesc/catdes/condes, datasets, matplotlib backend, examples, dist build.
- **Likely live with possible xfail'd parity on edge cases:** HMFA, DMFA, GPA.
- **Likely live without xfail:** plotly backend (no parity to chase), Sphinx site.
- **Always skipped:** TestPyPI upload (token-gated).

This is honest "everything tonight" — the deliverable is the full surface, with the xfail markers honestly recording where the night ran out of time on parity for the niche methods.

## 7. Subagent parallelism

Within batches that the main agent can split cleanly without a coherence cost, spawn `Agent` subagents:

- **Batch 2:** one subagent re-derives + downloads datasets while the main agent writes `tools/refresh_r_fixtures.R`.
- **Batches 3–7:** during numerical-parity tightening, one subagent can drive R from the command line to dump alternative options (`scale.unit=FALSE`, weight variations) while the main agent codes. Do not let subagents commit; they return diffs to the main agent.
- **Batch 13:** spawn a subagent per plot type for the snapshot baseline generation, then the main agent reviews and commits.
- **Batches 8–10:** spawn one subagent to extract the math from the FactoMineR PDF into a `notes/<method>.md` while the main agent implements; the main agent reads the note and discards it pre-commit (notes are scratch, not deliverables).

Never let a subagent push. Pushing happens only from the main agent, at batch boundaries.

## 8. Non-negotiables

- Clean-room only. No copies from `/Users/johnennis/aigora/clients/`.
- New code MIT. **No R source copied from FactoMineR (GPL).**
- Datasets re-derived from primary public sources; provenance recorded.
- `factominer-py/` strictly off the demo runtime path; `ml/` and `src/` untouched.
- `npm run lint` / `typecheck` / `build` and `python3 -m compileall ml scripts` must continue to pass at every commit.
- `NEXT_TELEMETRY_DISABLED=1` for any Node command.
- Do not pause for surveys, feedback prompts, update prompts.
- Use the xfail policy from §2 honestly. If a niche method's R-parity won't converge tonight, mark the test xfail with a clear reason, document the known limitation in the method's docstring + Sphinx page, and move on. Do not silently lower the tolerance to make a test green.

## 9. Read order on resume

1. `docs/elves/factominer-python-port-survival-guide.md`
2. This file
3. `docs/elves/factominer-python-port-execution-log.md`
4. `.elves-session.json`
5. `AGENTS.md`, `CLAUDE.md`
6. `factominer-py/README.md` and the most recent batch's test output
