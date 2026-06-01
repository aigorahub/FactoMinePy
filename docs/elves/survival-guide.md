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

- **Planned batches remaining:** 12 (7 of 20 enumerated batches done)
- **Stop allowed right now:** no
- **Why:** 7 done (A1–A4, B1–B3); 12 remain (B4–B5, C1–C3, D1–D4, E1–E3, F1).
- **Next required action:** confirm B3 zero-drift CI green, then start B4 (missing values + row
  weights). B4 folds in deferred FAMD `ind_sup` + GPA missing-values. Still deferred: Burt+quali_sup.
  Entropy check due ~after B5.

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

**Status:** Phase A + entropy + B1 + B2 + B3 done. MFA family + FAMD sup + MCA sup/Burt + GPA
unequal-width all parity-verified.

**Active batch:** B3 done → B4 (missing values + row weights).

**What was just finished:** B3 — GPA unequal-width configs + correlations + PANOVA; 16/16 GPA parity
vs live R (symmetric `_similarite` fixed the unequal-width simi). Equal-width unchanged. 205 passed /
2 skipped. Commits through `93e9bfb`. README/ROADMAP/CHANGELOG updated. GPA missing-values deferred to
B4. Earlier: Phase A, entropy check, B1 (FAMD sup), B2 (MCA sup/Burt).

**Single next action:** confirm B3 zero-drift CI green, then start B4 (missing values + row weights).

---

## Next Exact Batch

**Batch:** B4 — missing values + row weights

**Scope (from the plan + deferrals):** audit PCA/CA/MCA for R's missing-value handling and `row.w`
support; add the paths R supports + fixtures that exercise them. R FactoMineR has documented NA
handling (iterative imputation `imputePCA`-style, or the simpler complete-case/row-weight paths) and
`row.w` in several methods; today the port assumes complete data + uniform weights. **Folds in the
deferred items:** GPA missing values (the VMQTE path — `M`/`Cj` 0/1-diagonal metrics, `invgC=pinv(Cc)`,
pairwise-deleted RV/simi; spec captured in the B3 GPA research) and FAMD `ind_sup` (supplementary
individuals — compute the active scaling from active rows only, then project sup rows; spec in the B1
FAMD research).

**Suggested order (independent sub-tasks; can split if too large):** (1) PCA `row.w` (R's PCA takes
`row.w`; the port's PCA already accepts `row_w` — assert it against an R fixture with non-uniform
weights). (2) FAMD `ind_sup` (B1 deferral — the cleanest add). (3) PCA/MCA missing-value handling
(the largest — R's `MCA` NA→`.NA` category vs `imputeMCA`; PCA NA handling). (4) GPA missing values.

**Risk:** R's missing-value handling differs by method (NA-as-category in MCA vs iterative imputation
in PCA). Verify R's EXACT NA semantics per method before implementing; don't assume one approach.
This batch may be large — split into B4a/B4b if needed and record in the log.

**Rollback tag:** `elves/pre-batch-b4` (create before starting).

**Scope (from the plan):** in `factominer/gpa.py`, handle the two
`NotImplementedError` branches — (1) **missing values** (the VMQTE path), (2)
**unequal-width configurations** (groups of different column counts). Plus
**assert `correlations` and `PANOVA`** against R (currently computed/loosely
checked but not fully parity-asserted). Lift the GPA "no-missing, equal-width"
caveat from the README once verified. R's GPA is stochastic — keep the
established two-tier parity (RV/RVs/simi exact; consensus/Xfin rotation-invariant,
see test_gpa.py / learnings on GPA). Fixture: extend `tools/refresh_r_fixtures.R`
GPA dump (maybe a second synthetic dataset with unequal widths and/or an NA).

**Risk:** the multi-config Procrustes with unequal widths needs the general
centering/projection (not the equal-width shortcut `invgC = C/K`); R's GPA
stochastic multi-start means consensus/Xfin stay rotation-invariant-tier. PANOVA
is the Procrustes ANOVA table — verify its exact schema against R.

**Rollback tag:** `elves/pre-batch-b3` (create before starting).

**Scope (from the run-2 plan):**
1. **Assert MCA's sup blocks.** Run #1 shipped MCA `quanti.sup` / `quali.sup` code (`factominer/mca.py`
   routes through CA; PCA-style sup handling) but the final review flagged that the tea MCA fixture /
   tests never asserted those blocks. Add `tools/refresh_r_fixtures.R` dumps for MCA `quanti.sup` and
   `quali.sup` (the tea fixture already uses `MCA(tea, quanti.sup=19, quali.sup=c(20:36))`), and add the
   column-by-column assertions in `tests/test_mca.py`. NOTE: verify `mca.py` actually *populates*
   quanti_sup/quali_sup — it may only accept the args without computing the blocks; if so, implement
   them (route through the CA sup machinery / barycenters, mirroring PCA's quali.sup).
2. **Burt.** Verify `method="burt"` against R `MCA(..., method="Burt")` — either confirm parity or
   document the divergence. Update the README MCA row honestly (currently "Burt option exists but is
   not parity-verified").

**Fixture (license-clean):** extend the existing `mca/tea.json` dump (or add a sup-focused one) with
`quanti.sup`/`quali.sup`; add a Burt fixture `MCA(tea, method="Burt")` if pursuing Burt parity. All on
the already-bundled tea dataset.

**Risk:** MCA's `var$coord` is the STANDARD category coordinate (learnings [[L1]]) — the sup-category
barycenters and v.test follow the MCA conventions, not PCA's. Check whether mca.py's sup path uses the
right convention before asserting.

**Rollback tag:** `elves/pre-batch-b2` (create before starting).

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
