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

- **Planned batches remaining:** 4 (16 of 20 enumerated batches done; + B4b deferred work)
- **Stop allowed right now:** no
- **Why:** 16 done (A1–A4, B1–B5, C1–C3, D1–D3); 4 remain (D4, E1–E3, F1) + B4b.
- **Next required action:** start D4 (utility exports). Deferred: B4b, Burt+quali_sup, MFA reconst,
  CaGalt type=n/ellipses, meansComp, LinearModel Type-II/stepwise, textual stacked multi-spec.

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

**Status:** Phase A + B + C done; Phase D nearly done. **D1–D3 complete.** 16 of 20 batches;
everything parity-verified at the deterministic / supplementary bar.

**Active batch:** D3 done → D4 (utility exports). B4b (missing values + FAMD ind_sup) deferred.

**What was just finished:** D3 — `textual` (`textual.py`), free text → document×word contingency
table, verbatim from R; exact integer parity. Found R's misnamed `nb.words` frame ([[L25]]). 233
passed / 2 skipped; rpy2-parity green (run 26738229192). Commit `54952b9` + nb.words fix + close-out.
Earlier: Phase A, B1–B5, C1–C3, D1 (CaGalt), D2 (regression family).

**Single next action:** tag `elves/pre-batch-d4`, then start D4 (utility exports) — spec in the Next
Exact Batch section below.

---

## Next Exact Batch

**Batch:** D4 — utility exports. Mostly **expose + verify existing primitives**. Recommended scope:
`svd.triplet` + `tab.disjonctif` (+ `.prop`). Assess `simule`/`write.infile` (likely defer — see
below). R sources fetched (`svd.triplet.R`, `tab.disjonctif.R`, `tab.disjonctif.prop.R`, `simule.r`,
`write.infile.R`); decode via `gh api repos/cran/FactoMineR/contents/R/<name> --jq '.content' | base64 -d`.

**`svd_triplet(X, row_w=None, col_w=None, ncp=Inf)` — the weighted-SVD primitive (R `svd.triplet`):**
- `row.w <- row.w/sum(row.w)`; `ncp <- min(ncp, nrow-1, ncol)`; `Xw = t(t(X)·√col.w)·√row.w`.
- SVD of `Xw` (with the `ncol<nrow` vs transpose branch — for parity just `np.linalg.svd`).
- **Sign convention:** `mult = sign(colSums(V))` (0→1), applied to BOTH U and V (only when ncp>1).
- **Un-whiten:** `U <- U/√row.w`, `V <- V/√col.w`. Return `vs` (=d[1:ncp]), `U`, `V`.
- Build on `factominer/_svd.py` (`standard_svd` already does the SVD + a sign align — but check its
  sign rule matches `colSums(V)`; the port stores WHITENED U/V on results, so `svd_triplet` must
  return the UN-whitened R-convention U/V = whitened/√w, the same conversion used in CaGalt [[L23]]).
  Likely a thin new `factominer/_svd.py` public `svd_triplet` (or a small module) + export. Verify
  vs an R fixture (decathlon, with and without non-uniform row.w/col.w).

**`tab_disjonctif(df)` + `tab_disjonctif_prop(df)` — the indicator builders (R `tab.disjonctif.R`):**
- `tab.disjonctif`: the 0/1 disjunctive (one-hot) table with R's column naming. Already built inline
  in `mca.py`/`famd.py` and `predict.py:_build_indicator` — centralize a public version that matches
  R's column-label rule (the `y/n`/`Y/N` → `var.level` prefixing; read `tab.disjonctif.R` for the
  exact naming). `tab.disjonctif.prop` fills NAs with the column proportion (read the source).
- Fixture: `tab.disjonctif(tea[,1:4])` or a small factor frame; exact match (0/1 ints) + column names.

**`simule` / `write.infile` — ASSESS, likely DEFER:** `simule` (R `simule.r`) simulates data from a
PCA result — likely **stochastic** (rnorm) → would need a weaker tier or exclusion; read it and if
stochastic, defer like GPA/ellipses. `write.infile` writes a result to a text file (I/O formatting,
not analytic) → **out of scope** (record the decision, don't implement). Confirm by reading both.

**Parity bar:** `svd_triplet` vs (1e-9 coord-like); `tab.disjonctif` exact (integer + labels). License-
clean: reuse bundled `decathlon` (svd) and `tea`/`poison` (disjonctif).

**Rollback tag:** `elves/pre-batch-d4` (create before starting).

**Deferred (carry forward):** B4b = missing values (PCA/CA/MCA/GPA) + FAMD `ind_sup`; Burt +
`quali_sup`; MFA `reconst` (all-quanti); CaGalt `type="n"` + `conf_ellip`; `meansComp`; LinearModel
Type-II/AIC-BIC selection; textual stacked multi-spec; D4 `simule`/`write.infile` (assess).

**After D4:** E1–E3 (plots for the new methods — plot data-layer parity; E3 ggplot likely out of
scope), then F1 (release: README all-✅, version cut, final-review fan-out, tag → PyPI). **Never
merge — hand off PR #5 for the user.**

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
