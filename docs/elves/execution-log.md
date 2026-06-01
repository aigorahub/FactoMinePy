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

- **Last updated:** 2026-05-31 (A1 complete, parity-verified)
- **Current phase:** Batch A1 complete + CI-confirmed zero drift; Batch A2 (MFA completeness) in progress
- **Active batch:** A1 → done; next A2
- **Last completed batch:** A1 (MFA core) — 21/21 parity tests green vs live R
- **Next exact batch:** A2 (MFA completeness — partial axes, group$correlation, coord.partiel)
- **Active PR:** [#5](https://github.com/aigorahub/FactoMinePy/pull/5)
- **Collision tripwire (latest own HEAD):** `81c94be` (staging tripwire was `19c448b`)
- **Test baseline:** 123→144 passed, 2 skipped (the +21 are MFA parity tests; skip count unchanged)

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

## Batch A2 — MFA completeness — 2026-05-31 (IN PROGRESS: code done, awaiting CI fixture)

**Phase:** Implement complete; local green; rpy2-parity CI loop pending.
**Rollback tag:** `elves/pre-batch-a2` (pushed).

**Contract:** extend `factominer/mfa.py` with MFA's partial-factor-map machinery:
`ind$coord.partiel` (per-group partial individual coords, `(n·K)×ncp`), `group$correlation`
(weighted-ML correlation of partial vs global coords), `partial.axes` (coord/cor/contrib — each
group's separate principal axes vs the global axes), `inertia.ratio` (per-axis between/total
inertia). Reuses A1's `data`/`ponderation`/global-PCA/separate-analyses (now retained).

**Build on:** A1's global PCA (`pca.svd.U/V`, `pca.call["mean"]`/`["col_w"]`), the per-group
separate analyses (`separate[]`, newly kept), `data_cols_of_group`. New containers:
`Block.coord_partiel`, `Result.partial_axes` (Block), `Result.inertia_ratio` (Series),
`MFAGroup.correlation`.

**Source-verified (MFA.R):** coord.partiel L458-477 (`K·Xis·col.w·V`, Xis = group g centered /
others 0); group$correlation L478-483 (`cov.wt(..., method="ML")`); partial.axes L521-554
(separate ind coords standardized, projected on `svd$U`; contrib = coord²·sep_eig_ratio, col-norm
to 100; coord==cor since the tab is unit-variance); inertia.ratio L484-486.

**Local checks (pre-CI):** ruff clean; pytest 150 passed / 2 skipped (6 A2 tests no-op until the
extended fixture lands). **Barycenter invariant holds** (mean over groups of partial coords ==
global coord, max diff 7e-15) — the defining MFA property. partial.axes contrib columns sum to 100;
coord==cor. inertia.ratio in (0,1] as expected.

**Deferred (recorded):** `partial.axes$cor.between` (P×P cross-correlation of separate axes, with
R's inconsistent `Dim.1.group` labeling), `ind$within.inertia`/`within.partial.inertia`,
`summary.quanti`, `quali.var$coord.partiel`. Plus the A1 deferrals (sup groups, f/m types).

**Next:** push → trigger CI (extended `dump_mfa` regenerates `mfa/poison.json` with the A2
channels) → verify the 6 A2 tests pass vs fresh R → commit fixture → confirm zero drift.

---

## Batch A1 — MFA core — 2026-05-31 (COMPLETE — 21/21 parity vs live R)

**Phase:** Implement → Validate → Review → Document, all done. Parity-verified.
**Rollback tag:** `elves/pre-batch-a1` (pushed).
**Commits:** `8607b69` (implementation + test harness), `81c94be` (R fixture + schema fixes),
docs/close-out commit to follow.

**Validation (final):** ruff clean; sphinx -W builds; pytest **144 passed / 2 skipped**
(was 123/2 at baseline; +21 MFA parity tests, skip count unchanged → no tests disabled).
All 21 MFA channels match live R FactoMineR 2.14 at the bar: eig 1e-10, eig% 1e-8, svd 1e-9,
ind coord/cos2 1e-9 + contrib 1e-8, quanti.var coord/cos2/cor 1e-9 + contrib 1e-8,
quali.var coord/cos2 1e-9 + contrib 1e-8 + v.test 1e-6, group coord/cos2/dist2/Lg/RV 1e-9 +
contrib 1e-8.

**Review (adversarial-verify, the plan's hard-method rhythm):** two independent opus reviewers
read `mfa.py` against the R source — one on data-assembly/ponderation/global-PCA/eig/quanti.var/
quali.var, one on the group/Lg/RV block. **Zero parity bugs found.** Both confirmed the keystone
formulas (1/λ₁ eigenvalue weighting, `(1−p)/(λ₁·J)` categorical col.w, `√(p(1−p))` indicator
scaling, group$coord = fraction×eigenvalue, the Lg "MFA" row dividing by the global first
eigenvalue) and the internal cross-checks (group coords sum to eigenvalues per axis; active
contributions close to 100%; RV diagonal=1).

**First CI round** surfaced exactly one issue: `test_mfa_ind_dist` — R MFA's `res$ind` has no
`dist` (MFA.R:657), and `dump_block`'s fixed schema serialized the NULL as `{}`. Fixed faithfully:
dropped `dist` from MFA's ind block (schema parity) and removed the inapplicable test. See
learnings [[L15]]. No tolerance was loosened; no fixture was edited to pass.

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
- [x] ruff clean; sphinx -W builds; local pytest green (144 passed, 2 skipped).
- [x] MFA runs on canonical poison `group=c(2,2,5,6) type=c("s","n","n","n")`;
      internal check: group$coord sums to the eigenvalue per axis (Dim.1 = 3.0897 = eig₁).
- [x] **rpy2-parity** vs live R (eig 1e-10; coord/cos2/cor 1e-9; contrib 1e-8; v.test 1e-6) —
      **21/21 MFA tests pass**; CI run 26731204533 **green on both jobs (zero drift confirmed)** —
      the committed `mfa/poison.json` byte-matches freshly-generated live R output.

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

**Regression attestation:**
- **Cumulative diff vs baseline** (`19c448b...HEAD`): new `factominer/mfa.py`, `tests/test_mfa.py`,
  `tests/fixtures/r_outputs/mfa/poison.json`; additive edits to `_result.py` (new MFAGroup +
  Result.group), `__init__.py`/`_deferred.py` (MFA stub→live), `refresh_r_fixtures.R` + `conftest.py`
  (new fixture), `test_smoke.py` (MFA live, HMFA/DMFA still deferred), plus docs. No files changed
  outside batch scope; no deletions of product code.
- **Shared surfaces:** `_result.py` — purely additive (new `MFAGroup` dataclass; new optional
  `Result.group` field defaulting `None`). `grep` confirms `Result.group` is read only by `mfa.py`;
  all existing Block/SVD/Result consumers (pca/ca/mca/famd/gpa/hcpc/plot/desc) are untouched and
  still green. `MCA`/`PCA` reused read-only by MFA (no signature changes).
- **Test baseline:** 123→144 passed; skipped 2→2 (unchanged). Total only went up. No test disabled,
  weakened, or skipped to pass.
- **Confidence: HIGH.** Every channel matches live R at the deterministic bar; two independent
  adversarial source-reviews found no bugs; the only failure was a fixture-schema artifact fixed
  faithfully. MFA reuses the already-parity-verified PCA engine, so the blast radius is small.

**Docs updated:** README status table + prose (MFA ✅/✅), ROADMAP table, CHANGELOG [Unreleased],
learnings L12–L15.

**Deferred to A2 (recorded, not dropped):** `ind$coord.partiel`, `partial.axes`,
`group$correlation`, `inertia.ratio`, `summary.quanti`, supplementary groups (`num.group.sup`),
and `type` `"f"`/`"m"` groups (raise `NotImplementedError`).

**Commits:** `8607b69`, `81c94be`, + docs/close-out commit.

---
