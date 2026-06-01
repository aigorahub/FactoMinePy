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

- **Planned batches remaining:** 3 (17 of 20 enumerated batches done; + B4b deferred work)
- **Stop allowed right now:** no
- **Why:** 17 done (A1–A4, B1–B5, C1–C3, D1–D4 = Phases A–D complete, ALL analytic parity done);
  3 remain (E1–E3 plots [structural], F1 release) + B4b. E3 (ggplot) likely out of scope.
- **Next required action:** start E1 (plots for new methods — structural). Deferred: B4b,
  Burt+quali_sup, MFA reconst, CaGalt type=n/ellipses, meansComp, LinearModel Type-II/stepwise,
  textual stacked multi-spec, simule/write.infile.

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

**Status:** **Phases A–D complete — ALL analytic-method parity is done.** 17 of 20 batches.
Remaining: Phase E (plots — structural) + F1 (release). Everything analytic is parity-verified at the
deterministic / supplementary bar.

**Active batch:** D4 done → E1 (plots for the new methods — structural). B4b deferred.

**What was just finished:** D4 — `svd_triplet` + `tab_disjonctif` (`utils.py`), the weighted-SVD
primitive + the one-hot coder, parity-verified. 235 passed / 2 skipped; rpy2-parity green (run
26738742953). Commits `5bdf6bb`, `e336ba5` + close-out. Earlier: Phases A–C, D1 (CaGalt), D2
(regression family), D3 (textual).

**E1 scope already scouted (plot API uses `choix=`, not `kind=`):** `plot(res, choix="ind")` works
generically (via `plot_pca_ind`) for FAMD/MFA/CaGalt; `choix="var"` fails for MFA/CaGalt (they have
`quanti_var`, not `.var` → `plot_pca_var` hits `res.var=None`); HMFA/DMFA use custom result dataclasses
(`HMFAResult`/`DMFAResult`) that `plot()` doesn't accept. Parity here is **structural** (coords already
parity-verified) — no R numeric fixture; verify with smoke tests that `plot()` runs + draws the right
blocks.

**Single next action:** tag `elves/pre-batch-e1`, then start E1 — spec in the Next Exact Batch below.

---

## Next Exact Batch

**Batch:** E1 — plots for the new methods (**structural** — the coords are already parity-verified;
no R numeric fixture, verify with smoke tests that `plot()` runs + draws the right blocks). The plot
layer is `factominer/plot/` (`_data.py` + `matplotlib_backend.py` + `plotly_backend.py`); API is
`plot(res, choix="ind"|"var"|"biplot"|"scree"|"contrib", ...)`.

**Scope (smallest-first):**
1. **MFA / CaGalt `choix="var"`** — they have `quanti_var` (+ CaGalt `freq`), not `.var`. In
   `matplotlib_backend.plot()` / `plotly_backend.plot_plotly()`, when `res.var is None` and
   `res.quanti_var is not None`, route `choix="var"` to a quanti-var correlation circle using
   `res.quanti_var.coord`/`.cor`. (`plot_pca_var` reads `res.var.coord` — generalize it or branch.)
   `choix="ind"` already works generically for FAMD/MFA/CaGalt via `plot_pca_ind`.
2. **HMFA / DMFA** use custom dataclasses (`HMFAResult`/`DMFAResult`) that carry `ind`/`quanti_var`
   etc. but `plot()` is typed `Result | HCPCResult` and routes on `res.method`. Either (a) make those
   dataclasses expose the same `.method`/`.ind`/`.quanti_var` attributes plot reads (check
   `factominer/hmfa.py`, `dmfa.py`), or (b) add isinstance handling. `ind`/`scree` should then work.
3. **Smoke tests** `tests/test_plot_newmethods.py`: for FAMD/MFA/HMFA/DMFA/CaGalt, assert
   `plot(res, choix="ind")`, `"var"`, `"scree"` return an Axes/Figure without error and the scatter
   has the right point count (= n individuals / n variables). matplotlib `Agg` backend. No R fixture.

**Defer to E2/E3 (record, don't block E1):** the partial-axis plots (`plotMFApartial`,
`plotGPApartial`), `plot.CaGalt` ellipse overlays, `autoLab` smart label placement, `plotellipses`/
`ellipseCA` (run #1 already vertex-parity-verified `coord.ellipse`). **E3 (ggplot) = OUT OF SCOPE**
(no Python ggplot2; plotly is the analogue — record the decision).

**Parity bar:** structural only (plot runs, right blocks/counts). No deterministic R fixture.

**Rollback tag:** `elves/pre-batch-e1` (create before starting).

**Deferred (carry forward):** B4b = missing values (PCA/CA/MCA/GPA) + FAMD `ind_sup`; Burt +
`quali_sup`; MFA `reconst` (all-quanti); CaGalt `type="n"` + `conf_ellip`; `meansComp`; LinearModel
Type-II/AIC-BIC selection; textual stacked multi-spec; `simule` (stochastic) / `write.infile` (I/O,
out of scope); E2 partial/helper plots; E3 ggplot (out of scope).

**After E1:** E2 (plot helpers — autoLab/plotellipses/ellipseCA/partial plots; structural), then F1
(release: confirm README all-✅, decide version bump, final-review fan-out, update CHANGELOG). **F1's
tag → PyPI publish is a HAND-OFF — never tag/publish autonomously. Never merge — hand off PR #5 for
the user.**

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
