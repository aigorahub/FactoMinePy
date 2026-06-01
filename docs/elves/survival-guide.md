# READ THIS FILE FIRST AFTER ANY COMPACTION OR RESTART

> Survival Guide for **elves run #2 — complete FactoMineR feature parity**.
> Persistent memory across compactions. After any compaction, read this file
> before touching code. If it disagrees with your memory, trust this file.
>
> Read order after compaction: this file → `.elves-session.json` →
> `docs/elves/learnings.md` → `docs/plans/elves-run-2-full-parity.md` →
> `docs/elves/execution-log.md`.

---

## Mission

Close the remaining gap to full R FactoMineR 2.14 parity: implement and
parity-verify every analytically meaningful NAMESPACE export. ~22 batches over
6 phases (A MFA family, B completeness, C auxiliary, D long tail, E plotting,
F release). The full plan is `docs/plans/elves-run-2-full-parity.md`.

---

## Run Control

- **Run mode:** finite (defined scope = full parity), but large. No fixed deadline.
- **Stop policy:** blocker-only / completion. The user said "I don't care how long it takes" — that's a long budget, not open-ended; complete all phases, then Final Completion.
- **User intent:** "plan the complete closure of feature parity as an /elves run ... I don't really care how long it takes." Earlier standing instruction: **never merge** (the user merges).
- **Merge policy:** NEVER merge. No merge-on-green opt-in. Hand off PR for the user.
- **Checkpoint semantics:** none. **Actual stop conditions:** the plan's 4 hard stops (loosen a deterministic tolerance; 3 consecutive same-job CI failures; a method needs a new weaker parity tier; a new dataset has an unresolvable licensing concern), or all phases complete.
- **Final-response policy:** disallowed until all batches done or a hard stop fires.
- **Batch completion rule:** every batch ends with `update execution log → update survival guide → commit → push`.
- **Re-read rule:** after every commit + push, re-read this file before anything else.
- **Runaway threshold:** 5 same-file edits without progress → stop, rethink.

---

## Workspace Ownership (elves ≥ 1.11.0)

- **This run owns:** branch `feat/full-parity` in the dedicated worktree
  `/Users/johnennis/aigora/dev/FactoMinePy-full-parity`. Do not work in any
  other checkout of this repo, and do not let another agent share this one.
- **Collision tripwire:** branch tip at staging was **`19c448b`**. If
  `git rev-parse HEAD` or the remote branch tip later points at a commit this
  run did not create, another writer is in the checkout — STOP, treat as a
  collision (a Hard Stop), and surface it. Do not commit on top.
- **Baseline note:** this branch is based off `origin/docs/run-2-full-parity-plan`
  (= run #1 code + the run-2 plan), NOT `main`, because **PR #3 (run #1) is not
  yet merged** and `main` lacks FAMD/GPA/plotly that MFA builds on. The run-2
  PR is stacked on the plan branch and will retarget to `main` as PR #3 → #4
  merge. The baseline is correct regardless of merge order.

---

## Session Budget

- **Started:** _filled at launch_
- **User returns:** open / periodic check-ins. **Time budget:** very large ("don't care how long").
- **Batches remaining:** 22 of 22 (see plan).

---

## Stop Gate

- **Planned batches remaining:** 6 (13 of 20 enumerated batches done; + B4b deferred work)
- **Stop allowed right now:** no
- **Why:** 13 done (A1–A4, B1–B5, C1–C3, D1); 6 remain (D2–D4, E1–E3, F1) + B4b.
- **Next required action:** start D2 (regression family — D2a LinearModel+AovSum, D2b RegBest;
  defer meansComp). Deferred: B4b, Burt+quali_sup, MFA reconst, CaGalt type=n/ellipses.

---

## Effort Standard

- Work as hard on batch 22 as on batch 1. This is a long run; sustain effort.
- The parity bar (ROADMAP.md / the plan) is non-negotiable for deterministic methods. Never loosen a tolerance to make a test pass — that is a hard stop.
- When a batch completes, immediately take the next from the plan.

---

## Non-Negotiables

- **Never merge.** Hand off the PR; the user merges.
- **Never loosen a deterministic parity tolerance** (1e-10 eig, 1e-9 coord/cos²/cor/eta² active / 1e-7 sup, 1e-8 contrib, 1e-6 v.test, 1e-5 rel p-values). Stochastic/rotation-equivalent methods get an explicit weaker tier (like GPA) — surface the tier choice before shipping.
- **Never modify a test/fixture to make it pass.** Fix the code; if a fixture looks wrong, regenerate it from R via CI and investigate.
- **Never run destructive git** (`reset --hard`, `checkout .`, `clean -fd`, `push --force`, `rebase` on a pushed branch) or operate on another agent's branch/checkout.
- **R is not installed locally.** Every fixture goes through the `rpy2-parity` CI workflow_dispatch loop (edit `tools/refresh_r_fixtures.R` → push → `gh workflow run ci.yml --ref feat/full-parity` → wait → `gh run download <id> -n r-outputs-fresh` → commit fixture → confirm zero drift). Never fabricate fixture numbers.
- **No new third-party dataset without surfacing licensing** (the MFA `wine` decision — prefer a reproducible synthetic or reshape; if bundling `wine`, document provenance and flag it).

---

## R access loop (critical workflow)

1. Edit `tools/refresh_r_fixtures.R` to add the new method's fixture.
2. Commit + push the branch.
3. `gh workflow run ci.yml --repo aigorahub/FactoMinePy --ref feat/full-parity`.
4. `gh run watch <run-id> --exit-status`; then `gh run download <run-id> -n r-outputs-fresh`.
5. Extract `r_outputs_fresh.tar.gz`, commit the new fixture(s).
6. Run pytest locally against them; iterate the Python source.
7. Re-trigger; confirm the `r-fixture-drift` artifact shows zero drift for the new fixture (residual ~1e-16 singular-value noise is acceptable, per learnings).

3 consecutive `rpy2-parity` failures on the same job for the same root cause = hard stop.

---

## Tool Configuration

```yaml
lint: .venv/bin/ruff check factominer tests
typecheck: .venv/bin/mypy factominer || true   # advisory
test: .venv/bin/pytest -q
sphinx: .venv/bin/python -m sphinx -W -b html docs docs/_build/html
rpy2-parity-dispatch: gh workflow run ci.yml --repo aigorahub/FactoMinePy --ref feat/full-parity
review: github-pr-comments
notification: pr-comment
```

The venv is at `.venv/` in the worktree root (`pip install -e '.[dev]'`).

---

## Current Phase

**Status:** Phase A + B + C done; Phase D started. **D1 (CaGalt) complete.** 13 of 20 batches;
everything parity-verified at the deterministic / supplementary bar.

**Active batch:** D1 done → D2 (regression family). B4b (missing values + FAMD ind_sup) deferred.

**What was just finished:** D1 — `CaGalt` (type s/c), new `factominer/cagalt.py` + `freq` Result
slot. Thin orchestrator over PCA; required R's `svd.triplet` un-whitening for phi.stand/coord.ind,
a direct `quanti.var` (port PCA conflates coord/cor when unscaled), and a non-degenerate synthetic
fixture ([[L23]]). 225 passed / 2 skipped; rpy2-parity green (run 26737273383). Commits `1adc61b`,
`46faab4` + close-out. Earlier: Phase A, B1–B5, C1–C3.

**Single next action:** tag `elves/pre-batch-d2`, then start D2 — full spec (from the D2 research
subagent) in the Next Exact Batch section below.

---

## Next Exact Batch

**Batch:** D2 — regression family. **D2a = `LinearModel` + `AovSum`; D2b = `RegBest`; DEFER
`meansComp`.** numpy/scipy only — **do NOT add statsmodels** (heavyweight; its ANOVA/contrast
defaults don't match R's `contr.sum` Type-III layout anyway). Full D2 research report is in this
turn's transcript. R's `car`/`leaps` are FactoMineR `Imports`, so fixtures generate fine in CI.

**D2a — `LinearModel(formula, data, type="III", selection="none")` + `AovSum`:**
- R forces `options(contrasts=c("contr.sum","contr.sum"))` — **every coefficient/SS depends on
  sum-to-zero contrasts.** Coerce non-numeric cols to factors + droplevels. Fit OLS via
  `np.linalg.lstsq` on the contr.sum design matrix (reuse `predict.py:_build_indicator` for the
  one-hot, then map to sum contrasts; `condes.py:91-117` has the contr.sum Estimate idea).
- **Ftest table** (`car::Anova(model, type)`), cols `SS, df, MS, F value, Pr(>F)`; Type-III drops the
  intercept row. Type-III SS for a term = RSS increase when that term's columns are removed while all
  others stay. (Type-II + `selection="aic"/"bic"` step() = documented stretch/gap, not blocking.)
- **Ttest table** = `summary.lm$coef` (Estimate/Std.Error/t value/Pr(>|t|)) **rebuilt per level**: a
  k-level factor appends the omitted last level as `-sum(estimates)`, SE `sqrt(sum(cov[idx,idx]))`
  from `vcov = σ²(XᵀX)⁻¹`, p via `pt(.., resid_df)*2`; rownames `"<factor> - <level>"`, interactions
  ` : `-joined. **Fixture MUST include a 2+level factor AND an interaction** to exercise this.
- `lmResult` scalars: `r.squared`, `sigma`, `fstatistic` (value/numdf/dendf), and `aic`/`bic` via
  R's `extractAIC` = `n·log(RSS/n) + k·edf` (NOT the Gaussian-loglik AIC — match exactly).
- `AovSum(formula, data)` ≡ `LinearModel(type="III", selection="none")` returning only
  `{Ftest, Ttest}` — implement as a thin wrapper over the shared core, don't duplicate the loop.
- Output classes/names: `LinearModel` → `Ftest`, `Ttest`, `call`, `lmResult` (+`*Comp` when
  selection used); `AovSum` → `Ftest`, `Ttest`.

**D2b — `RegBest(y, x, int=TRUE, method="r2"|"Cp"|"adjr2", nbest=1)`:** all-numeric x (no contrasts).
R uses `leaps` (branch-and-bound best subset) but the observable output = best subset of each size by
RSS → reproduce with **exhaustive `itertools.combinations` + `lstsq`** (guard large p; fine for
decathlon's 10). Per size: refit, record `r.squared` + overall-F p-value `pf(F, numdf, dendf,
lower=F)`. Best-model choice: `r2`→min overall-F p; `Cp`→`argmin(Cp)` (Mallows, full-model MSE as
σ̂²); `adjr2`→`argmax(adjr2)`; ties → first index. Output `all` (per-size summary.lm), `summary`
matrix (`R2`,`Pvalue`, rows "Model with k variable(s)"), `best`.

**DEFER `meansComp`** — needs `emmeans` (estimated marginal means) + `multcompView` (compact-letter
display) + studentized-range Tukey; out of proportion to an EDA port. Record as its own future batch.

**Fixtures (license-clean, bundled):** `LinearModel`/`AovSum` on `poison` (numeric Age/Time + 2-level
factors Sick/Sex/Nausea): `LinearModel(Time~Sick+Sex+Nausea, type="III")` AND
`LinearModel(Time~Sick*Sex, type="III")` (interaction path) + `AovSum(Time~Sick+Sex+Nausea)`.
`RegBest` on `decathlon`: `x=decathlon[,1:10]`, `y=Points`, methods r2/Cp/adjr2. Dump Ftest/Ttest
(incl. reconstructed last-level rows)/lmResult scalars, and RegBest summary + best$r.squared/coef +
the chosen index. New `factominer/linear_model.py` (+ `AovSum`) and `factominer/reg_best.py`; export.

**Parity bar:** SS/F/coefficients/SE/t/R²/AIC/BIC at 1e-6 relative; p-values 1e-5 rel; df exact.

**Sharp edges:** contr.sum vs contr.treatment (use sum); Type-III SS term-drop mapping (test vs a
2-factor+interaction fixture); `extractAIC` formula (not loglik AIC); RegBest best-index tie-break
(first); singular designs. Reuse `predict.py:_build_indicator`, `condes.py` contr.sum idea.

**Rollback tag:** `elves/pre-batch-d2` (create before starting).

**Deferred (carry forward):** B4b = missing values (PCA/CA/MCA/GPA) + FAMD `ind_sup`; Burt +
`quali_sup`; MFA `reconst` (all-quanti); CaGalt `type="n"` + `conf_ellip`; D2 `meansComp` +
LinearModel Type-II/AIC-BIC selection.

---

## Rollback & Safety

1. Tag before each batch: `git tag elves/pre-batch-<id> && git push origin elves/pre-batch-<id>`.
2. Never force-push; never rebase the pushed branch; never merge.
3. If something goes badly wrong: create a recovery branch from the last good tag, document, stop.
4. Stage files by name; never `git add -A`.

---

## Plan & Log Paths

- **Plan:** `docs/plans/elves-run-2-full-parity.md`
- **Learnings:** `docs/elves/learnings.md` (run-1 lessons L1–L11 + process notes; extend, don't overwrite)
- **Execution log:** `docs/elves/execution-log.md`
- **Session JSON:** `.elves-session.json`
- **Branch:** `feat/full-parity` | **Worktree:** `/Users/johnennis/aigora/dev/FactoMinePy-full-parity`
- **PR:** #5 — https://github.com/aigorahub/FactoMinePy/pull/5
- **Collision tripwire:** `19c448b`

---

## After Any Compaction

1. Read this file; confirm Run Control, Stop Gate, Workspace Ownership.
2. Read `.elves-session.json` (`continuation_guard`, current batch, PR, tripwire).
3. Read `docs/elves/learnings.md` (R FactoMineR traps).
4. Read the plan; confirm scope.
5. Read the execution log; find the last completed batch.
6. Verify `git rev-parse HEAD` lineage is yours (collision check).
7. Resume from "Next Exact Batch". Don't redo completed work.

---

## Launch prompt (paste into a fresh Claude Code session)

```
/elves docs/plans/elves-run-2-full-parity.md

The run is staged. Worktree /Users/johnennis/aigora/dev/FactoMinePy-full-parity,
branch feat/full-parity (collision tripwire 19c448b). Session artifacts:
docs/elves/survival-guide.md, learnings.md, execution-log.md, .elves-session.json.

Work ONLY in that worktree on that branch. Start with Batch A1 (MFA core). R is
not installed locally — fixtures go through the rpy2-parity CI workflow_dispatch
loop. Parity bar + stop conditions are in the plan. Never merge.
```

---

# READ THIS FILE FIRST AFTER ANY COMPACTION OR RESTART
