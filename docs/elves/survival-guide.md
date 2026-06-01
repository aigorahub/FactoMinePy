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

- **Planned batches remaining:** 20 (A1 + A2 complete + parity-verified)
- **Stop allowed right now:** no
- **Why:** A1+A2 done; 20 batches remain (A3–A4, B1–B5, C1–C3, D1–D4, E1–E3, F1).
- **Next required action:** confirm A2 zero-drift CI green, then start A3 (HMFA) — first extend
  `mfa.py` with `weight_col_mfa` + `call["XTDC"/"col_w"/"group_mod"]`.

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

**Status:** Batches A1 + A2 COMPLETE — MFA fully parity-verified (27/27 vs live R). A3 (HMFA) next.

**Active batch:** A2 done → A3 (HMFA)

**What was just finished:** A1 (MFA core, 21 channels) + A2 (MFA completeness: coord.partiel,
group.correlation, partial.axes, inertia.ratio — 6 more channels). 150 passed / 2 skipped; ruff +
sphinx clean. Commits `8607b69`/`81c94be`/`caebd01` (A1), `0e5aaae`/`b69e136` (A2). Docs updated
(README/ROADMAP/CHANGELOG/learnings L12–L15). HMFA (A3) research spec captured.

**Single next action:** confirm A2 zero-drift CI green, then start A3 (HMFA). **A3 prerequisite:**
extend `mfa.py` to accept `weight_col_mfa` and expose `call["XTDC"]` / `["col_w"]` / `["group_mod"]`
(HMFA's `hweight` re-enters MFA per hierarchy level passing `weight.col.mfa`, multiplying in one
`1/λ₁` per level). Fixture: poison `H=[[2,2,5,6],[2,2]]`, type `[s,n,n,n]` (license-clean reshape).

---

## Next Exact Batch

**Batch:** A3 — HMFA (Hierarchical MFA)

**Scope:** `factominer/hmfa.py` (or extend MFA). HMFA = MFA with per-hierarchy-level `1/λ₁`
accumulation, then one weighted `PCA(scale_unit=False)` on the level-1-normalized `XTDC` with the
accumulated column weights. `H = list of per-level group counts` (`H[[1]]` = elementary group sizes
like MFA's `group`; `H[[h≥2]]` = #groups-of-previous-level per node). Ported helpers: `htabdes`
(expand group-of-groups → XTDC column counts), `hdil`, `hweight` (HMFA.R L41-56 — the keystone).
Outputs: `eig`, `ind` (+ `coord.partiel` per level), `quanti.var`, `quali.var`, `group$coord`
(LIST, one matrix per level), `group$canonical` (canonical correlations), `partial` (per-level
arrays). Remove the HMFA stub.

**A3 PREREQUISITE (do first):** extend `factominer/mfa.py` to (1) accept `weight_col_mfa` and thread
it into BOTH the separate-group analyses (multiply col weights before computing λ₁) AND the final
`ponderation`; (2) store `XTDC` (the `data` matrix), `col_w` (ponderation), and `group_mod` (expanded
per-group col counts) in the result `call` dict. HMFA's `hweight` re-calls `MFA(XTDC,
group=Hinter[[n]], type="c", weight.col.mfa=cw)` at each level ≥ 2 and reads `call$col.w` /
`call$group.mod` / `call$XTDC`. This is the single hardest parity point.

**Fixture (license-clean):** poison `H=list(c(2,2,5,6), c(2,2))`, type `c("s","n","n","n")`
(level-2 super-groups: description={desc,desc2}, signs={symptom,eat}); plus a pure-quanti sanity:
decathlon[:,1:10] `H=list(c(4,3,3), c(1,2))`, type all `"s"`. Needs a new `dump_hmfa` (group$coord is
a list-per-level, partial is a list-per-level of per-node arrays). Full research spec in the A3 entry
of the execution log / the HMFA research summary.

**Acceptance:** eig/ind/quanti.var/quali.var/group$coord(per level)/canonical to the deterministic
bar; ruff clean; rpy2-parity green.

**Risk:** the `hweight` per-level `1/λ₁` accumulation via `weight.col.mfa` (HMFA.R L51-52). Verify
`poids[[1]]`/`poids[[2]]` before trusting the full fixture. See [[L12]].

**Rollback tag:** `elves/pre-batch-a3` (create before starting).

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
