# READ THIS FILE FIRST AFTER ANY COMPACTION OR RESTART

> Survival Guide for **elves run #1 — low-risk all-green sweep**.
> Day-manager notes for the night-shift agent. Persistent memory across
> compactions. After any compaction event, read this file before touching
> any code. If this file disagrees with what you think you remember, trust
> this file. Your memory is gone; this is not.
>
> Recommended read order after any compaction: this file ->
> `.elves-session.json` -> `docs/elves/learnings.md` ->
> `docs/plans/elves-run-1.md` -> `docs/elves/execution-log.md`.

---

## Mission

Drop every 🚧 row in the README status table except the MFA family (MFA /
HMFA / DMFA) by porting **FAMD**, **GPA**, and the **plotly backend**,
then adding **plot-data parity tests** and bumping to **`v0.2.0.dev0`**.
All committed fixtures must remain byte-identical to live R FactoMineR
2.14 output. The 1.0 path is documented in [ROADMAP.md](../../ROADMAP.md).

---

## Run Control

- **Run mode:** finite
- **Stop policy:** explicit-user-stop, blocker-only, or completion of all 5 batches
- **User intent:** "Final batch (5) ends with `git tag v0.2.0.dev0 && git push origin v0.2.0.dev0`. The release.yml workflow auto-publishes to PyPI from there."
- **Checkpoint due by:** none — finite run, no fixed deadline
- **Checkpoint semantics:** none
- **May continue after checkpoint:** N/A
- **Actual stop conditions:** any "stop condition" in `docs/plans/elves-run-1.md`, three consecutive CI failures on the same job for the same root cause, or a batch needing to loosen a parity tolerance below `ROADMAP.md`'s bar.
- **Final-response policy:** disallowed until Batch 5 is merged or a hard stop fires
- **Batch completion rule:** every completed batch ends with `update execution log -> update survival guide -> commit -> push`. A batch is not complete while its finished work exists only in the working tree.
- **Re-read rule:** immediately after every commit and push, re-read this survival guide before doing anything else.
- **Continuation rule:** if work remains and `Actual stop conditions` are not met, continue without waiting for user acknowledgment.

---

## Session Budget

- **Started:** _to be filled when launch call begins_
- **User returns:** within ~24h (finite, no fixed deadline; user reviews on return)
- **Checkpoint expectation:** all 5 batches landed, `v0.2.0.dev0` published to PyPI
- **Time budget:** ~6–10 hours (estimate: ~1–2h per batch including CI wait time)
- **Average batch time so far:** N/A (no batches complete)
- **Batches remaining:** 5 of 5

---

## Stop Gate

- **Planned batches remaining:** 4
- **Stop allowed right now:** no
- **Why:** Batch 1 (FAMD) complete and parity-verified; Batches 2–5 remain
- **Next required action:** start Batch 2 (GPA port) — create rollback tag `elves/pre-batch-2`, fetch R/GPA.R, fan out research or implement directly

---

## Effort Standard

- Work as hard as you can for the full run. Do not be lazy.
- Maintain the same level of effort on the last batch as on the first.
- Do not settle for the minimum acceptable change. The parity bar is in
  [ROADMAP.md](../../ROADMAP.md) and is non-negotiable.
- When one batch is complete, immediately take the next from the plan.

---

## Forbidden Stop Reasons

- A checkpoint time was reached (there is no checkpoint)
- A commit or push succeeded
- CI is green
- A PR exists
- The user is silent or offline
- You wrote a useful summary
- The current batch is complete but later batches remain
- You feel unsure whether to continue

If one of these happens, update the docs, commit, push, re-read this file, and continue.

---

## Non-Negotiables

- **You never merge.** The user merges PR #N (once known) after Batch 5
  lands. Do not approve or fast-forward the merge yourself.
- **Never modify a test to make it pass.** Fix the code. If you believe
  a test or fixture is wrong, log it and stop.
- **Never loosen a parity tolerance** below the values in
  [ROADMAP.md](../../ROADMAP.md#parity-bar). 1e-10 eigenvalues, 1e-9
  coord/cos²/cor/eta², 1e-8 contrib, 1e-6 v.test, 1e-5 relative on
  p-values. Tolerance loosening is a hard stop.
- **Never run destructive git:** `git reset --hard`, `git checkout .`,
  `git clean -fd`, `git push --force`, `git rebase` on shared branches.
- **Fixture regeneration goes through the `rpy2-parity` CI workflow.** R
  is not installed locally. The loop is documented under "R access loop"
  below.
- **Never introduce regressions.** Existing 83 passing tests must stay
  passing. Total test count never decreases.

---

## R access loop (the critical workflow)

This is the workflow that replaces local R installation. Use it for every
batch that adds or updates an R-derived fixture.

1. Edit `tools/refresh_r_fixtures.R` to add the new method's fixture.
2. Stage + commit + push the branch.
3. `gh workflow run ci.yml --ref feat/elves-run-1 -f` (the workflow has
   `workflow_dispatch:` enabled and the rpy2-parity job runs from a
   dispatch trigger).
4. Wait for completion: `gh run watch <run-id> --exit-status`.
5. Download fresh fixtures: `gh run download <run-id> -n r-outputs-fresh`.
6. Extract `r_outputs_fresh.tar.gz` and commit only the new fixture
   files (don't overwrite existing ones unless intentional).
7. Run pytest locally against them; iterate Python source until parity
   holds.
8. Re-trigger rpy2-parity. Confirm `git diff tests/fixtures/r_outputs/`
   on the resulting artifact is 0 bytes (zero drift).

If 3 consecutive `rpy2-parity` runs fail on the same job for the same
root cause, that is a hard stop.

---

## Launch Readiness

- [x] Plan cleaned and saved at `docs/plans/elves-run-1.md`
- [x] Survival guide updated from the current plan (this file)
- [x] Learnings file initialized at `docs/elves/learnings.md`
- [x] Execution log initialized at `docs/elves/execution-log.md`
- [x] Branch created: `feat/elves-run-1`
- [ ] PR opened (handled as part of Batch 0 commit + push)
- [x] Preflight run, critical failures cleared (see execution log)
- [x] Run mode, return time, and non-negotiables recorded
- [x] Stop Gate initialized with `Stop allowed right now: no`
- [x] Launch prompt prepared (bottom of this file)

---

## Current Phase

**Status:** In progress

**Active batch:** Batch 2/5 (GPA port) — next

**What was just finished:** Batch 1 (FAMD) complete. `factominer/famd.py`
implemented as a weighted PCA wrapper; 18 FAMD parity tests pass against
live R FactoMineR 2.14 (`poison` fixture); README/CHANGELOG updated; suite
at 100 passed / 2 skipped.

**Single next action:** Batch 2 (GPA). Create `elves/pre-batch-2` tag,
read `husson/FactoMineR/R/GPA.R`, implement `factominer/gpa.py` (iterative
Procrustes), add a GPA fixture + tests, run the rpy2-parity loop.

---

## Active Compute

**No active paid or long-running compute.** Each `rpy2-parity` CI run
takes ~3 min; trigger on demand only. PyPI publish at end of Batch 5 is
also CI-driven.

---

## Next Exact Batch

**Batch:** 2: GPA port

**Scope:**
- New `factominer/gpa.py` implementing Generalized Procrustes Analysis (iterative orthogonal Procrustes with scaling across K configurations). R source: `husson/FactoMineR/R/GPA.R` (~150 lines).
- Update `tools/refresh_r_fixtures.R` with a GPA fixture (the FactoMineR `wine` dataset is the canonical GPA example — but `wine` is not bundled; check whether an existing bundled dataset can be reshaped into K configurations, else bundle `wine` with provenance, or pick a smaller documented GPA example).
- New `tests/test_gpa.py` asserting `consensus`, `Xfin`, `RV`, `simi`, `correlation`.
- Remove `GPA` stub from `factominer/_deferred.py`.
- README row + CHANGELOG entry.

**Acceptance criteria:**
- [ ] `pytest -q` green
- [ ] `ruff check factominer tests` clean
- [ ] `rpy2-parity` CI run: zero fixture drift
- [ ] Parity at ROADMAP tolerances after sign/rotation alignment

**Risk:** GPA needs K configurations (groups of columns). The dataset question is the first thing to settle — GPA's canonical example is `wine` with `group=`. Decide the fixture dataset before implementing. The Procrustes rotation makes sign/orientation alignment more involved than PCA's per-axis sign flip.

**Rollback tag:** `elves/pre-batch-2` _(create this before starting)_

---

## Post-Checkpoint Control Loop

After every commit and push, answer these questions before doing anything else:

1. What unfinished batch or task am I starting right now?
2. Did the user change stop behavior, checkpoint meaning, priorities, or scope since the survival guide was last rewritten? If yes, rewrite Run Control / Current Phase / Stop Gate / Next Exact Batch now.
3. Does the Stop Gate still say `Stop allowed right now: no`? If yes, continue immediately.
4. Am I allowed to stop? If the answer is anything other than a clear hard stop, explicit user stop, or true blocker, continue immediately.

---

## Documentation Triggers

Before closing a batch, explicitly decide which durable docs changed and why:

- **Behavior changed:** README status table, CHANGELOG, `docs/api/<method>.md`.
- **New repeatable pattern:** `docs/elves/learnings.md` (e.g., "MCA's standard-coord trap; FAMD has the same issue").
- **New trap:** `docs/elves/learnings.md` and propose ROADMAP.md "Known limitations" addition.
- **Reusable lesson:** `docs/elves/learnings.md`.

If none apply, record that no durable doc updates were needed.

---

## Tool Configuration

```yaml
lint: .venv/bin/ruff check factominer tests
typecheck: .venv/bin/mypy factominer || true   # advisory, not a gate
build: .venv/bin/python -m build
test: .venv/bin/pytest -q
sphinx: .venv/bin/python -m sphinx -W -b html docs docs/_build/html
rpy2-parity-dispatch: gh workflow run ci.yml --ref feat/elves-run-1 -f
review: github-pr-comments
notification: pr-comment
```

The Python venv lives at `.venv/` in the repo root and is already
populated with `pip install -e '.[dev]'`.

---

## Rollback and Safety Rules

1. **Create a rollback tag before every batch:**
   ```bash
   git tag elves/pre-batch-N
   git push origin elves/pre-batch-N
   ```
2. **Never force-push** the working branch.
3. **Never rebase** the working branch during a run.
4. **Never merge.** Not even a fast-forward. The user merges when they return.
5. **If something goes badly wrong**, stop and create a clean recovery branch from the last good tag:
   ```bash
   git checkout -b recovery/from-elves-pre-batch-N elves/pre-batch-N
   git push -u origin HEAD
   ```
6. **Stage specific files.** Never `git add -A`. Never `git add .`.

---

## Plan and Log Paths

- **Plan:** `docs/plans/elves-run-1.md`
- **Learnings:** `docs/elves/learnings.md`
- **Execution log:** `docs/elves/execution-log.md`
- **Roadmap:** `ROADMAP.md`
- **Session JSON:** `.elves-session.json`
- **Branch:** `feat/elves-run-1`
- **PR number:** #3 — https://github.com/aigorahub/FactoMinePy/pull/3
- **Plan hash at session start:** _filled when session JSON is initialized_

---

## After Any Compaction

1. Read this file. Confirm Run Control, Stop Gate, and Next Exact Batch.
2. Read `.elves-session.json` for current batch state, PR number, and `continuation_guard`.
3. Read `docs/elves/learnings.md` for any traps or conventions discovered during the run.
4. Read `docs/plans/elves-run-1.md`. Confirm scope hasn't changed.
5. Read `docs/elves/execution-log.md`. Find the last completed batch.
6. Resume from the "Next Exact Batch" above. Don't re-implement completed work.

---

## Launch prompt (paste this into a fresh Claude Code session)

```
/elves docs/plans/elves-run-1.md

The run is already staged. Branch feat/elves-run-1 exists locally and on
origin. Session artifacts are at docs/elves/survival-guide.md,
docs/elves/learnings.md, docs/elves/execution-log.md, and
.elves-session.json.

Start with Batch 1 (FAMD). Read the survival guide first.
```

---

# READ THIS FILE FIRST AFTER ANY COMPACTION OR RESTART
