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

- **Planned batches remaining:** 2 (18 of 20 enumerated batches done; + B4b deferred work)
- **Stop allowed right now:** no
- **Why:** 18 done (Phases A–D + E1); 2 remain (E2 plot helpers [structural], F1 release) + B4b.
  E3 (ggplot) is out of scope (recorded).
- **Next required action:** start E2 (plot helpers — structural) → then F1 (release prep). Deferred:
  B4b, Burt+quali_sup, MFA reconst, CaGalt type=n/ellipses, meansComp, LinearModel Type-II/stepwise,
  textual stacked multi-spec, simule/write.infile, E3 ggplot.

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

**Active batch:** E1 done → E2 (plot helpers — structural). B4b deferred.

**What was just finished:** E1 — structural plots for FAMD/MFA/HMFA/DMFA/CaGalt on both backends
(`choix="var"` → `quanti_var` fallback; getattr-guarded optional sup blocks for the custom HMFA/DMFA
result dataclasses). 30 plot smoke tests; 266 passed / 2 skipped. Commit `ea0902f`. Earlier: Phases
A–D (all analytic parity).

**Single next action:** tag `elves/pre-batch-e2`, then start E2 (plot helpers) — spec in the Next
Exact Batch below. **NOTE: the run's core mission (all analytic-method parity) is COMPLETE; E2 is
structural plot polish and F1 is release prep + hand-off.**

---

## Next Exact Batch

**Batch:** E2 — plot helpers (**structural**; coords already parity-verified, no R numeric fixture —
verify with smoke tests). Plot layer = `factominer/plot/` (`_data.py` + matplotlib/plotly backends).
**Lower-value polish — the core analytic-parity mission is already complete.** Keep scope tight.

**Scope (smallest-first; do what's cheap, defer the rest):**
1. **Partial-axis plot for MFA** — MFA's `res.ind.coord_partiel` (the per-(individual,group) partial
   coords, already parity-verified) → a `plotMFApartial`-style overlay: for each individual, draw a
   point per group + a line to the global point. Add as `choix="partial"` (or a small helper). Use the
   existing `_data.py` geometry. `plotGPApartial` is the GPA analogue (GPA has `Xfin` per config).
2. **`plotellipses` / `ellipseCA`** — `coord.ellipse` (the ellipse vertex generator) is ALREADY
   shipped + vertex-parity-verified (run #1); `plot(..., ellipse=True, habillage=...)` already draws
   them for PCA/MCA. Check it works for the new methods' ind maps; if a small generalization makes
   ellipses available there, do it. Don't re-port `coord.ellipse`.
3. **`autoLab` (smart non-overlapping label placement)** — a geometric label-repulsion algorithm.
   **Highest effort, lowest value** for a parity port (it's a cosmetic layout heuristic with no clean
   parity target). **Recommend DEFER/skip** unless trivial; record the decision. (Matplotlib's
   `adjustText` is the analogue but is a new dep — don't add it.)
4. **Smoke tests** in `tests/test_plot_newmethods.py` (extend it) for any new plot path added.

**Parity bar:** structural only. No deterministic R fixture (so no rpy2-parity round — lint-and-test
CI runs the smoke tests).

**Rollback tag:** `elves/pre-batch-e2` (create before starting).

**Deferred (carry forward):** B4b; Burt + `quali_sup`; MFA `reconst` (all-quanti); CaGalt `type="n"`
+ `conf_ellip`; `meansComp`; LinearModel Type-II/AIC-BIC selection; textual stacked multi-spec;
`simule`/`write.infile` (out of scope); `autoLab` (cosmetic); **E3 ggplot (OUT OF SCOPE — record).**

**After E2 → F1 (release prep):** confirm README status table all-✅ + honest tiers (GPA
rotation-invariant; plots structural); decide the version (the maintainer's standing ask keeps the
"experimental" warning — soften only with explicit approval, so likely a dev release like
`0.3.0.dev0`, NOT 1.0.0); finalize CHANGELOG; run the full suite + a final rpy2-parity green. **Then
STOP and hand off: F1's git tag → `release.yml` auto-publishes to PyPI — that publish is the USER's
call, NEVER do it autonomously. NEVER merge PR #5 — the user merges.** At Final Completion, `git rm`
the `docs/elves/*` + `.elves-session.json` operational artifacts from the PR (per process note P2)
so the merged diff is product-code only.

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
