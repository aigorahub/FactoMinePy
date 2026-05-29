# Execution Log — elves run #1

> Running record of everything elves does in this run. Reverse chronological
> (newest at top). Past entries are not edited. Reusable lessons get promoted
> to `learnings.md`; stable repo truths eventually move to `.ai-docs/*`.
>
> After a context compaction, this file tells you what is done so you don't
> repeat work. The survival guide tells you what to do next.

---

## Run Digest

- **Last updated:** 2026-05-29 (Batch 1 complete)
- **Current phase:** In progress
- **Active batch:** Batch 2/5 (GPA port) — next
- **Last completed batch:** Batch 1 (FAMD port)
- **Next exact batch:** Batch 2 (GPA port)
- **Active PR:** [#3](https://github.com/aigorahub/FactoMinePy/pull/3)
- **Docs promoted this run:** none yet
- **Latest Elves Report:** not generated yet

---

## Session Setup: 2026-05-18 (staging)

**Phase:** Staging complete
**Plan:** `docs/plans/elves-run-1.md`
**Survival guide:** `docs/elves/survival-guide.md`
**Learnings:** `docs/elves/learnings.md`
**Execution log:** `docs/elves/execution-log.md`
**Branch:** `feat/elves-run-1`
**PR:** [#3](https://github.com/aigorahub/FactoMinePy/pull/3) — opened immediately after the Batch 0 push, per elves convention
**Run mode:** finite | **User returns:** within ~24h, finite no fixed deadline
**Checkpoint semantics:** none | **Actual stop conditions:** any "stop condition" in `docs/plans/elves-run-1.md`, three consecutive same-job CI failures, or a tolerance-loosening requirement
**Active compute at launch:** none
**Continuation guard:** stop_allowed=no | remaining_batches=5 | checkpoint_is_stop=no | next_required_action=launch in a fresh Claude Code session

**Batch breakdown:**
1. Batch 1: FAMD port — implement `factominer.FAMD` matching FactoMineR 2.14 FAMD
2. Batch 2: GPA port — implement `factominer.GPA` (iterative Procrustes)
3. Batch 3: plotly backend — port matplotlib backend to plotly, structural parity
4. Batch 4: plot-data parity tests — extract plot data, R fixtures, both backends consume the same data layer
5. Batch 5: polish + v0.2.0.dev0 — README pruning, version bump, tag, PyPI publish via release.yml

**Preflight:**
- Git remote / push / `gh` auth: PASS (verified: origin URL = https://github.com/aigorahub/FactoMinePy.git, `gh auth status` green, push tested via prior session)
- Validation gate dry run: PASS (`.venv/bin/pytest -q` → 83 passed, 2 skipped on origin/main tip 6315896; `.venv/bin/ruff check factominer tests` → clean; `.venv/bin/python -m sphinx -W -b html docs docs/_build/html` → clean)
- Environment / sleep / notification checks: WARN — macOS dev machine, no caffeinate running. User should consider `caffeinate -d -i -m -s &` before walking away if the run will span hours. Not a blocker for staging.
- Notes:
  - R is not installed locally; fixture regeneration goes through the `rpy2-parity` CI workflow on `feat/elves-run-1` via `workflow_dispatch`. See survival guide "R access loop" for the exact sequence.
  - The previous round's parity work is the proven template — `tests/test_pca.py` / `test_mca.py` / `test_desc.py` are the structural references for the FAMD/GPA tests.
  - PyPI trusted publisher is already configured for project `factominer` from the previous PyPI publish on commit `71fb150`. Batch 5's tag push will auto-publish via `.github/workflows/release.yml`.

**Launch readiness:** READY

**Launch prompt:**
> /elves docs/plans/elves-run-1.md
>
> The run is already staged. Branch feat/elves-run-1 exists locally and on
> origin. Session artifacts are at docs/elves/survival-guide.md,
> docs/elves/learnings.md, docs/elves/execution-log.md, and
> .elves-session.json.
>
> Start with Batch 1 (FAMD). Read the survival guide first.

---

<!-- Batch entries land below this line, newest first. -->

## 2026-05-29 — Batch 2 (GPA): HARD STOP, decision needed

**Status:** HALTED pending a user decision. Rollback tag `elves/pre-batch-2`
created; no GPA source code written. Branch is clean at Batch 1's state
plus this status note and the saved research.

**The blocker (triggers the run's "tolerance below ROADMAP bar" hard stop):**
R FactoMineR's `GPA()` is **non-deterministic**. Confirmed by reading
`/tmp/GPA.R` + the research workflow (saved to
`docs/plans/gpa-research-findings.json`):
- `f1ter` (GPA.R:749, 586-666) runs P=5 random restarts — unseeded
  `sample()` config permutations, random column permutations, random
  sign-flips — and keeps the best-of-5 by residual loss.
- `procrustesbis` (GPA.R:289) uses `rnorm()` to complete the null-space
  basis when a config block is rank-deficient.
So the returned `consensus` / `Xfin` / `scaling` depend on R's RNG state.
Exact 1e-9 parity on those (the bar every other method meets) is not
achievable without replicating R's RNG in Python (infeasible: R's RNG ≠
NumPy's), nor by seeding (the seeds aren't comparable across languages).

**What IS deterministic and matchable:** `RV`, `RVs`, `simi` (computed
from the RAW configurations Xdd, GPA.R:765-812 — rotation/scale-invariant,
independent of the random restart). And `consensus`/`Xfin` can be compared
to R via rotation-invariant quantities (inter-point distance matrices) or
by Procrustes-aligning the Python output to R before comparing.

**Other GPA complexity** (from the research, all in
`docs/plans/gpa-research-findings.json`): 860-line source; reflections
allowed (general orthogonal H, not pure rotation); eigen(AᵀA) not svd(A);
two different tolerances (1e-7 first pass vs 1e-10 in f1ter); a separate
unported `coeffRV` (RV + bias-corrected rvstd); a 3D `Xfin` array + K×K
matrices that need a dedicated `GPAResult` dataclass (HCPCResult is the
precedent); the canonical `wine` dataset is not bundled (research
recommends a deterministic synthetic K-config CSV).

**Options presented to the user (awaiting choice):**
- A. Reorder — do Batch 3 (plotly) + Batch 4 (plot-data parity) now (both
  hit the clean exact bar), defer the GPA decision.
- B. Implement GPA with a two-tier parity story: Tier 1 exact (RV/RVs/simi
  to 1e-7) + Tier 2 rotation-invariant (consensus/Xfin via inter-point
  distances / Procrustes alignment). Port the deterministic `algogpa`
  core, skip the stochastic `f1ter`, seed R's fixture. Honest but a weaker
  parity guarantee than the other methods.
- C. Defer GPA to "Round 2" alongside the MFA family; keep it a documented
  stub. Ship FAMD + plotly + plot-data parity in run #1.

No tolerance was loosened and no GPA code was committed — halted per the
run's explicit hard-stop instruction.

## 2026-05-29 — Batch 1: FAMD port

**Batch:** 1/5: FAMD port
**Contract status:** all criteria met.

**Timing:** Implement ~50m (incl. research workflow) / Validate ~25m (2 CI cycles) / Review inline. Session elapsed ~1h20m.

**What changed:**
- `factominer/famd.py` (new): FAMD as an unscaled weighted PCA on the mixed `[standardized-quanti | centered/sqrt(prop)-scaled indicator]` matrix; post-processes quanti.var, quali.var, var summary, eta². Delegates the decomposition to `PCA(scale_unit=False)` (matches FAMD.R:124).
- `factominer/_result.py`: added `quanti_var` / `quali_var` Block fields.
- `factominer/__init__.py` + `_deferred.py`: FAMD imported from new module; removed from deferred stubs; fixed stale `docs/plans/factominer-python-port.md §2` ref → ROADMAP.md.
- `tools/refresh_r_fixtures.R`: `dump_famd` helper + FAMD(poison) stanza reading the committed CSV (row.names=1, stringsAsFactors=TRUE) for byte-identical input.
- `tests/conftest.py`: `r_famd_poison` fixture.
- `tests/test_famd.py` (new, 18 tests): column-by-column parity; ind block compared positionally (jsonlite drops poison's auto-rownames).
- `tests/test_smoke.py`: FAMD off the deferred-raises parametrize.
- `tests/fixtures/r_outputs/famd/poison.json`: committed fixture from live R FactoMineR 2.14.
- README + CHANGELOG: FAMD → ✅; active-vars-only caveat; parity count 83 → 100.

**Commands run:**
- `gh workflow run ci.yml --ref feat/elves-run-1` (run 26653687097) → fixture generation success, pytest 97 passed / 3 failed (label lookups only) → fixed → run 26653954372 (zero-drift confirm).
- `.venv/bin/pytest -q` → 100 passed, 2 skipped.
- `.venv/bin/ruff check factominer tests` → clean.
- `.venv/bin/python -m sphinx -W -b html docs docs/_build/html` → clean.

**Test results:** Lint PASS / Tests PASS (100 passed, 2 skipped) / Sphinx PASS / rpy2-parity confirm run 26653954372 GREEN. Fixture drift vs committed = a single residual singular value `svd/vs[15]` at 1.4e-16 (max rel diff on real values: 0.0). vs[15] is the first spurious dummy-coding axis (poison has 2+26−13 = 15 meaningful axes) ≈ 0; this is the documented machine-epsilon LAPACK noise on residual eigenvalues (same as the prior round's CA `svd/vs[4]`), below every tolerance and ignored by `test_famd_svd_vs` (which compares only `|vs|>1e-12`). Not re-committed — chasing a 1e-16 wiggle is pointless.

**Review findings:**
- The two FAMD traps (eig truncation to ncp; quali.var principal-coord transform) were caught pre-implementation via the research workflow + direct source read, so no numeric rework was needed.
- _No blocking findings._

**Decisions made:**
- Used the already-bundled `poison` dataset (2 quanti + 13 quali, 26 globally-unique category labels) as the FAMD fixture instead of bundling R's `wine` — avoids adding a new GPL-tabulated dataset and sidesteps label collisions.
- Scoped Batch 1 to active-variable FAMD. Supplementary vars (`sup.var`/`ind.sup`) raise nothing yet (the param isn't exposed); documented as a known limitation. Rationale: keeps the parity claim honest (active FAMD is fully verified) and the batch tight. Logged as a scout follow-up.
- R fixture reads the committed CSV rather than `data(poison)` to guarantee identical input without a local R to verify against.

**Regression attestation:**
- Cumulative diff vs main: new `factominer/famd.py`, `tests/test_famd.py`, fixture; additive fields on Result; FAMD moved out of stubs. No changes to PCA/CA/MCA/HCPC/desc source.
- Shared surfaces: `_result.Result` gained two optional fields (default None) — purely additive, existing constructors unaffected. `__init__.py` export list unchanged in shape (FAMD still exported, now from a real module).
- Test baseline: 83 → 100 passing (+17 FAMD; +1 net from smoke reparametrize −1 FAMD-deferred +18 FAMD... net new = 17), 2 skipped unchanged. Count only went up.
- Confidence: HIGH. Every FAMD numeric channel matched R at 1e-9/1e-10 on the first CI generation; the only failures were label-lookup artifacts, now fixed.

**Next steps:** confirm zero-drift run green, then Batch 2 (GPA).
