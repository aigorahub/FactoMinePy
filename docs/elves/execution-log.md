# Execution Log — elves run #2 (full FactoMineR parity)

> Reverse-chronological (newest at top). Past entries are not edited. Reusable
> lessons get promoted to `learnings.md` (which already carries run #1's L1–L11).
> After compaction, this file tells you what is done; the survival guide tells
> you what to do next.
>
> Run #1's execution log (FAMD/PD/PL/GPA/POLISH) lives in PR #3's history; this
> file is reset for run #2.

---

## Run Digest

- **Last updated:** 2026-05-31 (staging complete)
- **Current phase:** Staging — launch-ready
- **Active batch:** Batch 0 (session setup)
- **Last completed batch:** none (run #2)
- **Next exact batch:** A1 (MFA core)
- **Active PR:** [#5](https://github.com/aigorahub/FactoMinePy/pull/5)
- **Collision tripwire:** `19c448b`

---

## Session Setup: 2026-05-31 (staging)

**Phase:** Staging complete
**Plan:** `docs/plans/elves-run-2-full-parity.md`
**Survival guide:** `docs/elves/survival-guide.md`
**Learnings:** `docs/elves/learnings.md` (run #1 L1–L11 preserved)
**Execution log:** `docs/elves/execution-log.md`
**Branch:** `feat/full-parity`
**Worktree:** `/Users/johnennis/aigora/dev/FactoMinePy-full-parity` (dedicated, per elves ≥1.11.0)
**Baseline:** `origin/docs/run-2-full-parity-plan` (run #1 code + the run-2 plan), tip `19c448b`. NOT `main` — PR #3 (run #1) is unmerged, so main lacks FAMD/GPA/plotly that MFA builds on. The run-2 PR stacks on the plan branch and retargets to main as PR #3 → #4 merge.
**Run mode:** finite, very large budget ("don't care how long"). **Merge:** never (user merges).

**Batch breakdown (6 phases, ~22 batches):**
- A1 MFA core · A2 MFA completeness · A3 HMFA · A4 DMFA
- B1 FAMD sup vars · B2 MCA sup-block parity + Burt · B3 GPA edge cases · B4 missing values + row weights · B5 dimdesc CA/MCA
- C1 predict.* · C2 reconst + estim_ncp · C3 descfreq
- D1 CaGalt · D2 regression family · D3 textual · D4 utility exports
- E1 plots for new methods · E2 plot helpers (autoLab/plotellipses/ellipseCA) · E3 ggplot (likely out of scope)
- F1 release

**Preflight (in the worktree):**
- venv created + `pip install -e '.[dev]'` (incl. plotly): PASS (`factominer 0.2.0.dev0` imports).
- `pytest -q`: PASS — **123 passed, 2 skipped** (baseline; matches run #1's final state).
- `ruff check factominer tests`: clean.
- `gh auth status`: logged in (`john-aigora`), scopes include `repo` + `workflow`.
- caffeinate: recommend the user run `caffeinate -d -i -m -s &` for long unattended stretches.
- R: NOT installed locally — fixtures go through the `rpy2-parity` CI workflow_dispatch loop.
- PyPI trusted publisher already bound (from v0.2.0.dev0); the F1 release tag will auto-publish.

**Launch readiness:** READY. Stop allowed right now: NO.

**Launch prompt:**
> /elves docs/plans/elves-run-2-full-parity.md
>
> The run is staged. Worktree /Users/johnennis/aigora/dev/FactoMinePy-full-parity,
> branch feat/full-parity (collision tripwire 19c448b). Session artifacts under
> docs/elves/. Work ONLY in that worktree on that branch. Start with Batch A1
> (MFA core). R is not installed locally — fixtures go through the rpy2-parity CI
> workflow_dispatch loop. Parity bar + stop conditions are in the plan. Never merge.

---

<!-- Batch entries land below this line, newest first. -->

## Batch A1 — MFA core — 2026-05-31 (IN PROGRESS: code done, awaiting CI fixture)

**Phase:** Implement complete; Validate (local green) done; rpy2-parity CI loop pending.
**Rollback tag:** `elves/pre-batch-a1` (pushed).

**Contract (behaviors):**
- `factominer/mfa.py` implements `MFA(X, group, type, ncp, name_group)` for active
  groups, uniform row weights, types `"s"`/`"c"`/`"n"` (frequency `"f"` / mixed `"m"`
  raise `NotImplementedError` — no fixture exercises them; deferred).
- Outputs: `eig`, `ind` (coord/cos2/contrib/dist), `quanti.var` (coord/cos2/contrib/cor),
  `quali.var` (coord/cos2/contrib/v.test), `group` (coord/contrib/cos2/dist2 + the
  `(K+1)×(K+1)` Lg/RV matrices), `svd`.
- `group$correlation`, `ind$coord.partiel`, `partial.axes`, `inertia.ratio`,
  `summary.quanti`, and supplementary groups (`num.group.sup`) are **A2 scope** —
  not implemented here (num_group_sup raises NotImplementedError).

**Build on (reuse, verified):**
- Global eigen-step delegated to `factominer.PCA(scale_unit=False, col_w=ponderation,
  quali_sup=raw_factors)` — exactly as R delegates to `FactoMineR::PCA`. This gives
  ind, var→quanti.var, quali.sup→quali.var(coord/cos2/v.test), eig, svd for free, all
  already parity-tested. Per-group λ₁ via `PCA`(s/c) / `MCA`(n) separate analyses.
- New container `MFAGroup` in `_result.py`; `Result.group` field added.

**Acceptance criteria:**
- [x] ruff clean; sphinx -W builds; local pytest green (124 passed, 23 skipped).
- [x] MFA runs on canonical poison `group=c(2,2,5,6) type=c("s","n","n","n")`;
      internal check: group$coord sums to the eigenvalue per axis (Dim.1 = 3.0897 = eig₁).
- [ ] **rpy2-parity zero drift** vs live R (eig 1e-10; coord/cos2/cor 1e-9; contrib 1e-8;
      v.test 1e-6) — PENDING CI fixture generation.

**Pre-implementation survey / source verification:**
- Read R `MFA.R` (master) L1-40 (funcLg/moy.p/ec), L180-320 (data assembly + ponderation),
  L340-500 (global PCA, eig slice, group/Lg/RV). Two research agents (R-source + literature
  triangulation) converged on the keystone: group weight = 1/λ₁ (eigenvalue, not singular
  value); categorical column = standardized centered indicator `(1[i∈k]−p)/√(p(1−p))` with
  col.w `(1−p)/(λ₁·J)`; group$coord = contrib-fraction × eigenvalue.
- Dataset decision: **canonical poison MFA** (already-bundled, provenance-documented) — the
  license-clean reshape the plan preferred over bundling `wine`. No new dataset → the
  licensing non-negotiable is satisfied with nothing to surface.

**Fixture loop:** added `dump_mfa` + the poison MFA block to `tools/refresh_r_fixtures.R`,
`r_mfa_poison` conftest fixture, `tests/test_mfa.py` (22 column-by-column tests, skip until
fixture lands). Next: push → `gh workflow run ci.yml --ref feat/full-parity` → download
`r-outputs-fresh` → commit `tests/fixtures/r_outputs/mfa/poison.json` → confirm zero drift.

**Commit:** _pending (mid-implementation push to trigger CI)_

---
