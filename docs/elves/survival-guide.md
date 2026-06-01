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

- **Planned batches remaining:** 10 (9 of 20 enumerated batches done; + B4b deferred work)
- **Stop allowed right now:** no
- **Why:** 9 done (A1–A4, B1–B5 = Phase A+B complete); 10 remain (C1–C3, D1–D4, E1–E3, F1) + B4b.
- **Next required action:** start C1 (predict.* family). Deferred: B4b (missing values + FAMD
  ind_sup), Burt+quali_sup. **Entropy check due now** — run at the C1 boundary.

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

**Status:** Phase A + entropy + B1–B5 done. **Phase A + B complete.** 9 of 20 batches; everything
parity-verified at the deterministic bar.

**Active batch:** B5 done → C1 (predict.* family). B4b (missing values + FAMD ind_sup) deferred.

**What was just finished:** B5 — wired `dimdesc` CA + MCA branches. MCA routes through the existing
condes path (added `active_frame` to MCA's call); CA is a self-consistency test (R 2.14's
`dimdesc(CA)` is broken on R 4.x). Handled R's extra `call` element in the MCA dimdesc result. 212
passed / 2 skipped; rpy2-parity green (run 26734779119), zero drift. Commits through `06e3559` +
close-out. Earlier: Phase A (MFA/HMFA/DMFA), entropy, B1 (FAMD sup), B2 (MCA sup/Burt), B3 (GPA
unequal-width), B4 (PCA row.w).

**Single next action:** tag `elves/pre-batch-c1`, then start C1 (predict.PCA/MCA/FAMD/MFA).

---

## Next Exact Batch

**Batch:** C1 — `predict.*` family (project held-out individuals onto a fitted model)

**Scope (from the plan):** implement `predict_pca`, `predict_mca`, `predict_famd`, `predict_mfa` —
each projects NEW individuals (rows not used to fit) onto an existing model's axes, returning
`coord`, `cos2`, and (PCA/MCA/MFA) `dist` / (FAMD) `dist2`. One batch covers all four. Fixtures:
fit on a train slice, predict a held-out slice, compare to R.

**IMPORTANT — the C1 research subagent read the WRONG checkout** (main, not this worktree) and
falsely claimed FAMD/MFA "don't exist." They DO exist here (`factominer/famd.py`, `mfa.py` — built
in A1/B1). The R-algorithm half of its report (below) is fetched from GitHub and is reliable; its
Python-machinery / file:line claims are stale — re-verify against THIS worktree before coding.

**R projection recipe (verbatim from `husson/FactoMineR` master, the reliable part):**
- **predict.PCA:** `nd <- (newdata - centre)/ecart.type; coord <- (t(t(nd)*col.w)) %*% svd$V;
  dist2 <- rowSums(t(t(nd^2)*col.w)); cos2 <- coord^2/dist2`. `centre/ecart.type/col.w/svd$V` are
  the TRAINING values. Output `coord, cos2, dist=sqrt(dist2)`. **This is the SAME math as the
  existing PCA `ind_sup` projection — reuse/extract a shared helper, don't duplicate.**
- **predict.MCA:** build `tab.disjonctif(newdata)` forced to TRAINING column set+order (absent
  categories → zero columns); `somme.row = rowSums = #active vars`; `tab <- tab/somme.row`;
  `coord <- tab %*% svd$V`; `dist2 <- rowSums(t((t(tab)-marge.col)^2/marge.col))`;
  `cos2 <- coord^2/dist2`. Output `coord, cos2` (**no dist**). `coord` is the **PRINCIPAL** coord
  (same scale as `ind$coord`), NOT the standard `var$coord`. Needs `marge.col` (CA col margin) +
  the active categorical frame stashed on the MCA result. Does NOT require the deferred MCA
  `ind_sup` — predict IS that projection.
- **predict.FAMD:** quanti block `(x-centre)/ecart.type`; quali block `(disjonctif - prop)/sqrt(prop)`
  (prop = training category proportions); `cbind`, `coord <- tab %*% svd$V`;
  `dist2 <- rowSums(tab^2)` (UNWEIGHTED); `cos2 <- coord^2/dist2`. Output `coord, cos2, dist2`
  (element literally named `dist2` but holds `sqrt(dist2)`).
- **predict.MFA:** per group, process by its method using that group's separate-analysis training
  centre/scale (quanti) or training marge.col (quali), then `sweep(tab,2,sqrt(col.w),"*")` and
  `coord <- tab %*% (global.pca$svd$V * sqrt(col.w))`; `dist2 <- rowSums(tab^2)`. Output
  `coord, cos2, dist=sqrt(dist2)`.

**Column-name quirk:** PCA/MFA use `"Dim.1"` (dot); **MCA/FAMD use `"Dim 1"` (space)** — the
`_as_df` conftest loader already tolerates both, but assert against the right one per method.

**Build on (re-verify in THIS worktree):** the PCA `ind_sup` block (extract a shared
`_project_individuals` helper used by both sup-ind and predict); the MCA→CA `svd.V` + `marge_col`;
FAMD's stashed active scaling (means/sds/category proportions); MFA's per-group `col_w` + global
`svd.V`. Check what each result's `call` dict already carries; add only what's missing.

**Sign convention:** projected `coord` inherits `svd.V` signs → compare to R with
`align_to_reference` per axis (as every coord test does). `cos2`/`dist` are sign-invariant. Parity
bar for projected quantities: **1e-7** (sup tier).

**Fixture plan (license-clean, already-bundled datasets):** PCA on `decathlon[1:20,1:10]` predict
`[21:23]`; MCA on `tea[1:250,1:18]` predict `[251:255]` (verify no unseen category in test rows —
widen train slice if so); FAMD on `poison` train/test; MFA on `poison` canonical grouping
train/test. Append a `dump_predict` helper to `tools/refresh_r_fixtures.R`.

**Risk:** the disjunctive-table rebuild forcing training column order (MCA/FAMD) is the most
error-prone step — use the training categorical dtype's category list so absent categories still
emit zero columns in the right positions. MCA principal-vs-standard coord (don't ×√eig). FAMD's
`dist2`-named-but-sqrt output. Full C1 research report is in this turn's transcript.

**Rollback tag:** `elves/pre-batch-c1` (create before starting).

**Entropy check:** due now (~C1 boundary). At the C1 start: stop idle jobs, rotate oversized logs,
archive completed execution-log entries if the file is long, confirm learnings/.ai-docs current.

**Deferred (carry forward):** B4b = missing-value handling (PCA/CA/MCA/GPA) + FAMD `ind_sup`;
Burt + `quali_sup` combination. Slot into the long tail (Phase D) or fold into C1 if the predict
work naturally surfaces the FAMD/MCA sup-projection machinery.

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
