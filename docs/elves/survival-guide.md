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

- **Planned batches remaining:** 19 (A1+A2+A3 complete + parity-verified)
- **Stop allowed right now:** no
- **Why:** A1–A3 done; 19 batches remain (A4, B1–B5, C1–C3, D1–D4, E1–E3, F1).
- **Next required action:** confirm A3 zero-drift CI green, then start A4 (DMFA, last Phase-A
  method). Entropy check due after A4 (3 batches since last).

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

**Status:** Batches A1+A2+A3 COMPLETE — MFA + HMFA parity-verified (41 channels vs live R). A4 next.

**Active batch:** A3 done → A4 (DMFA), the last Phase-A method.

**What was just finished:** A1 (MFA core), A2 (MFA completeness), A3 (HMFA — 14/14 first-pass parity;
extended `mfa.py` with `weight_col_mfa` + call exposure, built `hmfa.py` on the MFA/PCA engines).
164 passed / 2 skipped; ruff + sphinx clean. Commits through `d0cf12d`. Docs updated
(README/ROADMAP/CHANGELOG/learnings L16–L17). DMFA (A4) research spec captured.

**Single next action:** confirm A3 zero-drift CI green, then start A4 (DMFA). DMFA =
per-group-standardized stacked data → `PCA(quali_sup=grouping factor)` → DMFA-specific group block
`group$coord[j,s] = v_sᵀ Cov_j v_s / λ_s`, `coord.n` (÷ group's λ₁), `cos2`, plus `var.partiel` /
`cor.dim.gr` / `Cov`. Reuses PCA wholesale (~50-60 new lines). NOT MFA's `1/λ₁` weighting.
Fixture: `DMFA(decathlon, num.fact=13, quanti.sup=c(11,12))` (Competition factor) — license-clean.

---

## Next Exact Batch

**Batch:** A4 — DMFA (Dual MFA)

**Scope:** `factominer/dmfa.py`. `DMFA(don, num_fact, scale_unit=True, ncp=5, quanti_sup, quali_sup)`.
`num_fact` = column index of the grouping factor; it splits individuals into `ng` groups. Algorithm
(DMFA.R): (1) per-group center+scale each level's sub-table with that group's own mean/sd
(`scale()`), build `Cov[[j]]` = `cor`(scale_unit) or `cov` of the per-group sub-table; (2) vertically
stack the per-group-centered data, prepend the factor; (3) `res.pca = PCA(stacked, quali_sup=[factor],
quanti_sup=...)` — a plain unweighted PCA (PCA's own `scale_unit` stays True, decoupled from DMFA's);
(4) **reorder `ind` back to original row order** (DMFA.R L49-52); (5) DMFA group block:
`group$coord[j,s] = v_sᵀ Cov_j v_s / λ_s` where `v_s` = `res.pca.var.coord[:,s]` (the LOADINGS, not
V_tilde) and `λ_s` = global eig; `group$coord.n[j,s] = coord/λ₁(Cov_j)`; `group$cos2 = coord²/Σλ(Cov_j)²·100`;
plus `var.partiel[[j]]=cor(Xc_j, FS_j)`, `cor.dim.gr[[j]]=cor(FS_j)`, `Cov`, `Xc`. Remove the DMFA stub.

**Reuse:** PCA wholesale for eig/ind/var/quanti.sup/svd; ~50-60 new lines for the per-group
centering + the group trace block. New `DMFAResult` (or extend) with `group.coord/coord_n/cos2`,
`var_partiel`, `cor_dim_gr`, `Cov`, `Xc`.

**Hardest parity point:** `group$coord` trace `v_sᵀ Cov_j v_s / λ_s` — `V` is `var.coord` (loadings),
`Cov_j` uses n−1 (`scale()`/`cor`/`cov`), and three different normalizers (global λ_s, group λ₁,
Σλ²). DMFA does NOT use MFA's `1/λ₁` group weighting — per-group standardization instead ([[L16]]).

**Fixture (license-clean):** `DMFA(decathlon, num.fact=13, scale.unit=TRUE, quanti.sup=c(11,12))`
(Competition factor: Decastar n=13 / OlympicG n=28; 10 events active, Rank/Points sup). Optional
active-only sanity: `DMFA(decathlon[,c(1:10,13)], num.fact=11)`. New `dump_dmfa`.

**Acceptance:** eig/ind/var/group(coord/coord.n/cos2)/cor.dim.gr to the deterministic bar; ruff
clean; rpy2-parity green.

**Rollback tag:** `elves/pre-batch-a4` (create before starting).

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
