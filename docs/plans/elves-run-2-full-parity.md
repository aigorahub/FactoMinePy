# Elves run #2 plan — complete FactoMineR feature parity

**Mission:** close the remaining gap between FactoMinePy and R FactoMineR 2.14
so that every analytically meaningful NAMESPACE export is implemented and
parity-verified. This is a large, finite run (~22 batches across 6 phases).
Run length is not a constraint; correctness and parity are.

**Starting point:** `v0.2.0.dev0` (run #1: PCA, CA, MCA, FAMD, HCPC, GPA,
dimdesc/catdes/condes, matplotlib + plotly backends, R-exact ellipses).

**Prerequisite:** **merge PR #3 first.** This run branches from `main` *after*
run #1 is merged, so the baseline already has FAMD/GPA/plotly. Do not branch
from `feat/elves-run-1`.

---

## Run isolation (elves ≥ 1.11.0)

One run = one branch = one worktree. Stage in a dedicated git worktree:

```bash
git fetch origin main
git worktree add -b feat/full-parity ../FactoMinePy-full-parity origin/main
```

Record the branch tip at staging; stop if HEAD or the remote moves to a commit
this run did not create. One PR for the whole run; the user merges it.

---

## Parity bar (unchanged from ROADMAP.md — non-negotiable)

Deterministic methods: eigenvalues 1e-10; coord/cos²/cor/eta² 1e-9 (active),
1e-7 (supplementary); contrib 1e-8; v.test 1e-6; p-values 1e-5 relative.
Fixtures byte-identical to live R FactoMineR 2.14 via the `rpy2-parity` CI
workflow. **R is not installed locally — every fixture goes through CI**
(the run #1 loop: edit `tools/refresh_r_fixtures.R` → push →
`workflow_dispatch` → download `r-outputs-fresh` → commit → confirm zero
drift). Where a method is inherently stochastic or rotation-equivalent
(as GPA was), use an explicit, documented weaker tier rather than loosening
the deterministic bar.

## Per-batch workflow shape

Each method batch follows run #1's proven rhythm: a **research fan-out**
(3 parallel agents: R-source algorithm / port-primitive reuse / fixture+test
strategy) → implement on the existing primitives → the rpy2-parity CI loop →
docs. The hard methods (MFA, predict family) additionally get an
**adversarial-verify** fan-out (one checker per component against the R
source) before the CI loop. A **final-review** fan-out gates the release.

---

## Phase A — The MFA family (the keystone gap)

MFA is the largest single method (`MFA.R` 850 lines; `plot.MFA.R` 1485).
HMFA and DMFA reuse its primitives, so A1/A2 are the heavy lift.

### Batch A1 — MFA core
- `factominer/mfa.py`: groups of variables, each group normalized by its first
  singular value, then a global weighted PCA over the concatenated weighted
  blocks. Support `type` per group (`"s"` standardized-quanti, `"c"`
  centered-quanti, `"n"` categorical → MCA-style indicator, `"f"` frequency).
- Output: `eig`, `ind` (global coord/cos2/contrib), `quanti.var`, `quali.var`,
  `group` (group coordinates + contrib + RV-to-global), `svd`.
- Reuse: the PCA/MCA/FAMD scaling primitives and `coeffRV` from `gpa.py`.
- Fixture: `MFA(wine, group=..., type=...)` — **bundle the `wine` dataset**
  (it is the canonical MFA example; reproducible-synthetic won't exercise the
  mixed-type group logic the way wine does). Document provenance; or, if a
  license-clean mixed-group dataset can be reshaped from the existing bundle,
  prefer that.
- Acceptance: eig/ind/quanti.var/group coords to the deterministic bar.
- **Risk:** the group-normalization (divide each block by its first singular
  value) and the partial-axis machinery are the traps; MFA is where the
  MCA standard-vs-principal-coordinate lesson and the FAMD scaling lesson both
  recur. Adversarial-verify each component.

### Batch A2 — MFA completeness
- Partial factor maps (`ind$coord.partiel`), `partial.axes`, `group$correlation`
  / `group$dist2` / `group$cos2`, `inertia.ratio`, `summary.quanti`.
- Fixture extends A1's dump. Acceptance: every remaining MFA block at the bar.

### Batch A3 — HMFA (`HMFA.R` 209 lines)
- Nested groups (`group = list(list(...), ...)`). Built entirely on MFA
  primitives from A1/A2.
- Fixture: `HMFA` on a nested-group dataset. Remove the `HMFA` stub.

### Batch A4 — DMFA (`DMFA.R` 108 lines)
- The "dual" MFA view (configuration of partial clouds across a grouping
  factor). Reuses MFA primitives. Remove the `DMFA` stub.

---

## Phase B — Completeness inside shipped methods

### Batch B1 — FAMD supplementary variables
- Add `sup_var` / `ind_sup` to `factominer/famd.py` (FAMD.R has the full sup
  machinery already read in run #1; the quanti.sup/quali.sup transforms route
  through PCA's sup handling plus the FAMD-specific quali transform).
- Fixture: `FAMD(poison, sup.var=...)`. Drop the "active-only" README caveat.

### Batch B2 — MCA supplementary-block parity + Burt
- Add `tools/refresh_r_fixtures.R` dumps for MCA `quanti.sup` / `quali.sup`
  blocks and assert them in `tests/test_mca.py` (run #1 shipped MCA sup code
  but never asserted it — the final review flagged this).
- Verify `method="burt"` against R `MCA(..., method="Burt")`; either confirm
  parity or document the divergence. Update the README MCA row honestly.

### Batch B3 — GPA edge cases
- Missing values (VMQTE path) and unequal-width configurations (the two
  `NotImplementedError` branches), plus assert `correlations` and `PANOVA`
  against R. Lift the GPA "no-missing, equal-width" caveat.

### Batch B4 — Missing values + row weights
- Audit PCA/CA/MCA for R's missing-value handling and `row.w` support; add the
  paths R supports and fixtures that exercise them. (R FactoMineR has
  documented NA handling in several methods; today the port assumes complete
  data + uniform weights.)

### Batch B5 — dimdesc on CA / MCA
- Wire the CA/MCA branches of R's `dimdesc` (run #1's `dimdesc` leans on PCA's
  stashed call payload; CA/MCA need their own path — `dimdesc.R` has a
  dedicated CA branch). Fixtures for `dimdesc(CA_res)` and `dimdesc(MCA_res)`.

---

## Phase C — High-value auxiliary functions

### Batch C1 — `predict.*` (project new data)
- `predict.PCA` (22), `predict.MCA` (29), `predict.FAMD` (52), `predict.MFA`
  (44). Each projects new individuals onto an existing model's axes. Small,
  high-value; one batch covers all four. Fixtures: fit on a train slice,
  predict a held-out slice, compare to R.

### Batch C2 — `reconst` + `estim_ncp`
- `reconst` (41): low-rank reconstruction of the original table from a PCA/CA/
  MFA result. `estim_ncp`: estimate the number of components (GCV / generalized
  cross-validation). Fixtures vs R.

### Batch C3 — `descfreq` + descriptive completeness
- `descfreq` (49): describe the rows of a frequency table by their columns
  (the CA analogue of catdes). Plus any gaps in catdes/condes the run surfaces.

---

## Phase D — Secondary methods / long tail

### Batch D1 — `CaGalt` (101)
- Correspondence Analysis on Generalized Aggregated Lumped Tables.

### Batch D2 — Regression family
- `LinearModel` (198), `AovSum`, `RegBest`, `meansComp` (26). These are the
  ANOVA/regression helpers FactoMineR ships. Lower-traffic but part of full
  parity. May split if D2 is too large.

### Batch D3 — `textual`
- Text-analysis builder (document × word frequency tables feeding CA). Larger
  scope; verify against R's `textual`.

### Batch D4 — Utility exports
- `svd.triplet` (104, the weighted-SVD primitive — likely already covered by
  `_svd.py`; expose + verify), `tab.disjonctif` / `tab.disjonctif.prop`
  (expose the indicator builder), `simule`, `write.infile`.

---

## Phase E — Plotting depth

### Batch E1 — plots for the new methods
- `plot.MFA` (1485 — the data layer, not pixel parity), `plot.HMFA`,
  `plot.DMFA`, `plotMFApartial`, `plotGPApartial`, `plot.CaGalt`, on the
  existing `_data.py` + both backends. Structural parity.

### Batch E2 — plot helpers
- `autoLab` (187, smart non-overlapping label placement), `plotellipses`,
  `ellipseCA` (131), `prefpls`, `graph.var`. Structural / geometric parity
  where a derived quantity exists (as with `coord.ellipse`).

### Batch E3 — ggplot-style output (optional)
- R offers `graph.type="ggplot"`. Python has no ggplot2; the plotly backend is
  the closest analogue and already exists. Likely **out of scope** — record the
  decision rather than chase a non-Python idiom.

---

## Phase F — Release

### Batch F1 — v1.0.0 (or v0.3.0.dev0)
- README status table all-✅ (every analytic method live + parity-verified;
  honest tiers for GPA rotation-invariance and structural plots).
- Decide whether full parity warrants dropping "experimental" and cutting
  **1.0.0**, or another dev release. The maintainer's standing ask to keep an
  experimental warning is respected — soften only with explicit approval.
- Final-review fan-out (parity claims, CHANGELOG, version, docs xrefs) → tag →
  release.yml auto-publishes to PyPI (trusted publisher already bound).

---

## Explicitly out of scope (record, don't silently drop)

- `graph.type="ggplot"` output (no Python ggplot2; plotly is the analogue).
- The `Rcmdr` GUI plugin, `print.*` console formatters, LaTeX/`xtable` output.
- Pixel-exact plot images (we do structural + derived-quantity parity).

---

## Stop conditions (hard stops → write status note, halt, escalate)

1. A batch needs to loosen a **deterministic** tolerance below the bar.
2. Three consecutive `rpy2-parity` failures on the same job for the same root
   cause.
3. A method is inherently stochastic/non-deterministic (like GPA) and needs a
   new weaker-but-honest parity tier — surface the tier choice before shipping.
4. A new bundled dataset would introduce a licensing concern that can't be
   resolved with a synthetic substitute — surface before committing the data.

## Ordering & dependencies

```
A1 MFA core ── A2 MFA completeness ──┬── A3 HMFA
                                     └── A4 DMFA
B1..B5  (independent of A; can interleave)
C1..C3  (predict needs the models; after A for predict.MFA)
D1..D4  (independent; long tail)
E1..E3  (after the methods they plot exist)
F1 release (last)
```

A1 is the critical path and the highest-risk batch — do it first and verify
hard. B-phase items are independent and can fill CI-wait gaps. The run is
sequenced A → B → C → D → E → F, but the coordinator may interleave
independent batches to keep momentum during CI waits.

## Estimated scale

~22 batches. MFA (A1/A2) and the plot.MFA data layer (E1) are the multi-day
pieces; predict/reconst/descfreq/meansComp are small. No fixed deadline.

## Launch

After PR #3 is merged, in a fresh Claude Code session:

```
/elves docs/plans/elves-run-2-full-parity.md

Stage per elves ≥1.11.0: create a dedicated worktree + branch
feat/full-parity off origin/main, open one PR, then start Batch A1 (MFA
core). R is not installed locally — every fixture goes through the
rpy2-parity CI workflow_dispatch loop. Parity bar and stop conditions are
in the plan. Never merge.
```
