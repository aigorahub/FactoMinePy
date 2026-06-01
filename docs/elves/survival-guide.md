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

- **Planned batches remaining:** 7 (12 of 20 enumerated batches done; + B4b deferred work)
- **Stop allowed right now:** no
- **Why:** 12 done (A1–A4, B1–B5, C1–C3 = Phase A+B+C complete); 7 remain (D1–D4, E1–E3, F1) + B4b.
- **Next required action:** start D1 (CaGalt). Deferred: B4b (missing values + FAMD ind_sup),
  Burt+quali_sup, MFA reconst (all-quanti only). Entropy check due ~D-phase boundary (archive log).

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

**Status:** **Phase A + B + C complete.** 12 of 20 batches; everything parity-verified at the
deterministic / supplementary bar.

**Active batch:** C3 done → D1 (CaGalt). B4b (missing values + FAMD ind_sup) deferred.

**What was just finished:** C3 — `descfreq` (hypergeometric description of frequency-table rows),
new `factominer/desc/descfreq.py`, verbatim from R; parity-verified. Also corrected a flaky GPA
PANOVA test to its stochastic tier ([[L22]] — R's GPA isn't reproducible across CI runs even with
set.seed). 221 passed / 2 skipped; rpy2-parity green. Commits `6c77eeb`, `0b51a00` + close-out.
Earlier: Phase A, B1–B5, C1 (predict.*), C2 (reconst + estim_ncp).

**Single next action:** tag `elves/pre-batch-d1`, then start D1 (CaGalt) — full spec in the Next
Exact Batch section below (from the D1 research subagent).

---

## Next Exact Batch

**Batch:** D1 — `CaGalt` (Correspondence Analysis on Generalized Aggregated Lumped Tables)

**Scope:** `CaGalt(Y, X, type="s", conf_ellip=False, nb_ellip=100, level_ventil=0, sx=None,
graph=False, axes=(0,1))`. Y = n×p frequency/lexical table; X = n×k covariates. `type`: `"s"`
(quanti scaled, default), `"c"` (quanti centred), `"n"` (qualitative → indicator). Full research
report is in this turn's transcript (D1 subagent). **NOTE the real R args are `nb.ellip` +
`level.ventil`, NOT nperm/level.conf.**

**Algorithm (CaGalt = a thin orchestrator over PCA, verbatim from R `CaGalt.R`):**
- `P = Y/sum(Y)`; `PI. = rowSums(P)` (individual masses), `P.J = colSums(P)` (frequency masses).
- Covariate analysis weighted by `PI.`: for `type≠"n"`, standardize `X` with `PI.`-weighted
  mean/sd (`_scaling.center_scale(X, scale_unit=type=="s", row_w=PI.)`), and `phi.stand =
  diag.X$svd$U` where `diag.X = PCA(X, scale_unit=type=="s", ncp, row_w=PI.)`. For `type="n"`,
  `phi.stand` = whitened left vectors of the `PI.`-weighted centred indicator (build via `_svd.py`
  primitives — DON'T need MCA row_w, which the port lacks).
- Build: `L = sweep(P' @ phi.stand, 1, P.J, "/")` (p×ncp), `T = P' @ X`, `C = (X·√PI.)'(X·√PI.)`
  (Gram), `W = sweep(T @ pinv(C), 1, P.J, "/")` (`ginv` = `np.linalg.pinv`).
- **Inner decomposition:** `diag.L = PCA(cbind(L, W), quanti_sup=W cols, scale_unit=False, ncp,
  row_w=P.J)`. Everything re-projects off this:
  - `eig ← diag.L.eig`; `freq` (coord/cos2/contrib) ← `diag.L.ind`; `quanti.var ←
    diag.L.quanti_sup` (already has coord/**cor**/cos2 in the port); `quali.var ←
    diag.L.quanti_sup` coord+cos2 (type="n").
  - `ind` by transition: `coord.ind = (P' @ diag.L.svd.U) / PI.[:,None]`; `cos2.ind =
    coord²/rowSum(coord²)`.

**Build on (reuse, verified worktree paths):** `pca.py` `PCA` already takes `row_w`, `scale_unit`,
`ncp`, `quanti_sup` (quanti_sup returns coord/cor/cos2 — exactly what quanti.var needs) and exposes
`res.svd.U`. `_scaling.center_scale` = R's `mean.p`/`sd.p`. `np.linalg.pinv` = R `ginv`.

**Gaps (additive):** (1) add `freq: Block | None = None` to `Result` (`_result.py`). (2) new
`factominer/cagalt.py` + export. (3) a shared `_tab_disjonctif` helper with R's column naming (for
type="n"). (4) **Defer** `level_ventil>0` and `conf_ellip=True` (the ellipses are a **stochastic
bootstrap** — exclude, like GPA; raise/no-op). Implement `type="s"/"c"` first, then `type="n"`.

**Fixture (license-clean — NO bundled dataset exists; `health` is GPL + 115 cols):** build a small
synthetic `datasets/data/cagalt_synth.csv` (n≈12 × [6 freq cols Y | 3 quanti cols X], fixed numpy
seed, MIT — mirror `gpa_synth` + PROVENANCE). Add `load_cagalt_synth()`. Two R calls:
`CaGalt(Y, Xs, type="s")` and `CaGalt(Y, factor(round(Xn)), type="n", level.ventil=0)`, both
`conf.ellip=FALSE`. Dump eig/ind/freq/quanti.var (s) or quali.var (n). **Do NOT dump `ellip`.**

**Parity bar:** deterministic blocks (eig/ind/freq/quanti.var/quali.var coord·cor·cos2·contrib) at
the strict tier (eig 1e-10; coord/cos2/cor 1e-9; contrib 1e-8); coord sign-aligned per axis.

**Sharp edges:** two weight vectors — `PI.` weights the covariate analysis, `P.J` weights the main
analysis AND row-divides L/W (the double `sweep(…,P.J,"/")` then `row_w=P.J` is intentional). `pinv(C)`
is load-bearing (C is deliberately rank-deficient). `ind` cos2 = `coord²/rowSum(coord²)` over kept
axes (NOT a chi-square distance). quali.var labels follow `tab.disjonctif` naming. Signs inherited
from the inner PCA (already FactoMineR-aligned).

**Rollback tag:** `elves/pre-batch-d1` (create before starting).

**Deferred (carry forward):** B4b = missing values (PCA/CA/MCA/GPA) + FAMD `ind_sup`; Burt +
`quali_sup`; MFA `reconst` (all-quanti); CaGalt `level_ventil`>0 + `conf_ellip` bootstrap ellipses.

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
