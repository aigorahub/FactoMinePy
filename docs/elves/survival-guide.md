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

- **Planned batches remaining:** 9 (10 of 20 enumerated batches done; + B4b deferred work)
- **Stop allowed right now:** no
- **Why:** 10 done (A1–A4, B1–B5, C1); 9 remain (C2–C3, D1–D4, E1–E3, F1) + B4b.
- **Next required action:** start C2 (reconst + estim_ncp). Deferred: B4b (missing values + FAMD
  ind_sup), Burt+quali_sup. Entropy check done at C1 boundary (tree clean, logs OK).

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

**Status:** Phase A + B done; Phase C started. **C1 (predict.*) complete.** 10 of 20 batches;
everything parity-verified at the deterministic / supplementary bar.

**Active batch:** C1 done → C2 (reconst + estim_ncp). B4b (missing values + FAMD ind_sup) deferred.

**What was just finished:** C1 — `predict.PCA/MCA/FAMD/MFA` (`factominer.predict`). One shared
`_project_scaled` helper; per-method training-stat scaling. MFA needed R's idiosyncratic categorical
predict scaling (`(1[cat]-2·marge.col)/ec`, centred at 2p/J), distinct from the fit parametrization
([[L20]]). PCA's `ind_sup` refactored onto the shared helper. 216 passed / 2 skipped; rpy2-parity
green (run 26735782046). Commits `bfa74a8`, `17dada0` + close-out. Earlier: Phase A, B1–B5.

**Single next action:** tag `elves/pre-batch-c2`, then start C2 (reconst + estim_ncp).

---

## Next Exact Batch

**Batch:** C2 — `reconst` + `estim_ncp`

**Scope (from the plan):**
- **`reconst(res, ncp)`** — low-rank reconstruction of the original table from a PCA / CA / MFA
  result, using the first `ncp` axes. R `reconst.R` (~41 lines). For PCA:
  `Xhat = (ind.coord[,1:ncp] %*% t(var.coord[,1:ncp]) / sqrt(eig)... )` then un-scale by
  `ecart.type` and add back `centre` — i.e. `Xhat[i,j] = centre_j + ecart.type_j · Σ_{d≤ncp}
  F_id·G_jd/λ_d`? **Read R `reconst.R` for the exact rank-`ncp` formula and which coords it uses**
  (it likely reuses `svd$U`/`svd$V`/`svd$vs` directly: `Xhat = U[,1:ncp] diag(vs[1:ncp]) V[,1:ncp]'`
  then un-whiten by `/sqrt(row.w)/sqrt(col.w)`, un-scale, re-centre). CA's reconstruction is in the
  chi-square metric. The port stores `res.svd` (U_tilde/vs/V_tilde) + `call` centre/scale/row_w/col_w
  for PCA — everything needed. Returns a DataFrame the shape of the active table.
- **`estim_ncp(X, ncp.min, ncp.max, scale, method)`** — estimate the number of PCA components by
  GCV / generalized cross-validation (the "Smooth" / "GCV" criteria). R `estim_ncp.R`. Returns the
  chosen `ncp` + the criterion curve. This is a model-selection routine over PCA reconstructions.

**Build on:** `res.svd` (already `U_tilde`/`vs_full`/`V_tilde`), `res.call` (`mean`/`scale`/`row_w`/
`col_w`/`active_frame`). `reconst` is essentially `_project_scaled` run backwards — a low-rank
`U diag(vs) V'` un-whitened/un-scaled. `estim_ncp` loops `reconst` over candidate `ncp`. Likely a
new `factominer/reconst.py` (+ maybe `estim_ncp` alongside, or in a small `_ncp.py`). Export both.

**Fixtures (license-clean):** `reconst(PCA(decathlon[,1:10]), ncp=2)` → `reconst/pca_decathlon.json`
(the n×p reconstructed matrix); `reconst(CA(children), ncp=2)` if CA reconst is in scope;
`estim_ncp(decathlon[,1:10], ...)` → `estim_ncp/decathlon.json` (the chosen ncp + criterion vector).
Add a `dump_reconst`/`dump_estim_ncp` to `tools/refresh_r_fixtures.R`.

**Parity bar:** reconst is a deterministic linear map → **1e-9** on the reconstructed entries (it's
just coords × loadings). estim_ncp's criterion curve → 1e-7 relative; the chosen integer `ncp` must
match exactly.

**Risk:** R's `reconst` may reconstruct in the *scaled* space vs the original units — check whether
it re-adds `centre` and multiplies by `ecart.type` (PCA) or works in the CA chi-square metric. For
`estim_ncp`, R has multiple criteria (`"GCV"`, `"Smooth"`) — verify which is the default and match
its exact GCV formula (the residual-variance / penalty expression). Read both R sources first.

**Rollback tag:** `elves/pre-batch-c2` (create before starting).

**Deferred (carry forward):** B4b = missing-value handling (PCA/CA/MCA/GPA) + FAMD `ind_sup`;
Burt + `quali_sup` combination. Slot into the long tail (Phase D).

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
