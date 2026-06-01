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

- **Planned batches remaining:** 1 (19 of 20 done; + B4b deferred work). **F1 is the last batch.**
- **Stop allowed right now:** no (F1 release prep remains). After F1's prep, **STOP + hand off** —
  do NOT tag/publish/merge (those are the user's).
- **Why:** 19 done (Phases A–E; E3 ggplot out of scope); 1 remains (F1 release prep) + B4b.
- **Next required action:** start F1 (release prep — confirm README all-✅, version=dev release,
  finalize CHANGELOG, final review). Deferred: B4b + the option-level items (Burt+quali_sup, MFA
  reconst, CaGalt type=n/ellipses, meansComp, LinearModel Type-II/stepwise, textual multi-spec,
  simule/write.infile, autoLab, E3 ggplot).

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

**Active batch:** E2 done → **F1 (release prep — the LAST batch)**. B4b deferred.

**What was just finished:** E2 — MFA partial-individuals plot (`choix="partial"`, from the
parity-verified `coord_partiel`); ellipses already work on the new methods. autoLab/plotGPApartial
deferred (cosmetic). 267 passed / 2 skipped. Commit `25fb541`. **Phases A–E complete** (all analytic
parity + structural plots). Earlier: Phases A–D, E1.

**Single next action:** tag `elves/pre-batch-f1`, then start F1 (release prep) — spec in the Next
Exact Batch below. **NOTE: F1 is PREP ONLY — confirm releasable state, finalize docs/version. The git
tag → PyPI publish and the PR #5 merge are the USER's actions; never do them autonomously. After F1
prep, the run is COMPLETE — leave a reactivation handoff and stop.**

---

## Next Exact Batch

**Batch:** F1 — release prep (the LAST batch). **PREP ONLY — never tag/publish/merge autonomously.**

**Steps:**
1. **Confirm releasable state:** run `pytest -q` (expect 267 passed / 2 skipped) + `ruff check` +
   `python -m sphinx -W -b html docs docs/_build/html` (docs build clean). Trigger ONE final
   `rpy2-parity` CI (`gh workflow run ci.yml --ref feat/full-parity`) and confirm green (the GPA
   fixture intrinsically "drifts" — that's expected per [[L22]]; tests stay green).
2. **README:** confirm the status table is all-✅ for every analytic method with honest tiers (GPA
   ⚠️ rotation-invariant; plots structural). Keep the "experimental" warning (maintainer's standing
   ask — soften only with explicit user approval). Optionally add a short "Newly added in this run"
   line listing MFA family / CaGalt / regression / textual / predict / reconst / estim_ncp / descfreq
   / utilities.
3. **Version:** likely a **dev release** (e.g. bump `__version__` in `factominer/__init__.py` +
   `pyproject.toml` from `0.2.0.dev0` → `0.3.0.dev0`) since the experimental warning stays — do NOT
   cut 1.0.0 without explicit approval. Decide + apply the bump, note it in CHANGELOG.
4. **CHANGELOG:** finalize the `[Unreleased]` section (it already lists every addition); consider
   renaming it to the chosen version with today's date, or leave `[Unreleased]` for the user to stamp.
5. **Final review:** optionally a review fan-out (parity claims, CHANGELOG accuracy, version, docs
   xrefs). Then write the **reactivation handoff** in the execution log (branch/PR, final status,
   remaining deferred items, the exact resume prompt).

**THEN STOP — Final Completion / hand-off:**
- **NEVER** `git tag` / trigger `release.yml` / publish to PyPI — that is the USER's call.
- **NEVER** merge PR #5 — the user merges.
- Per process note P2, at Final Completion `git rm` the `docs/elves/*` + `.elves-session.json`
  operational artifacts from the branch so the merged PR diff is product-code only (keep
  `docs/plans/...`). Do this as the LAST commit, only when truly finishing — OR leave them and tell
  the user, since removing them loses the resume state if more work is wanted. **Default: leave them
  and flag for the user** unless you are certain the run is fully done.

**Rollback tag:** `elves/pre-batch-f1` (create before starting).

**Deferred (record in the handoff — option-level, not whole methods):** B4b (missing values +
FAMD `ind_sup`); Burt + `quali_sup`; MFA `reconst` (all-quanti); CaGalt `type="n"` + `conf_ellip` +
`level_ventil`; `meansComp`; LinearModel Type-II SS + aic/bic stepwise; textual stacked multi-spec;
`tab.disjonctif.prop`; `simule`/`write.infile` (out of scope); `autoLab` + `plotGPApartial`
(cosmetic plots); E3 ggplot (out of scope).

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
