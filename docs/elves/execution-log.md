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

- **Last updated:** 2026-05-31 (B1 complete, parity-verified)
- **Current phase:** Phase A done + entropy check done; Phase B underway (B1 done, B2 next)
- **Active batch:** B1 → done; next B2 (MCA sup-block parity + Burt)
- **Last completed batch:** B1 (FAMD sup vars) — 26/26 parity tests green vs live R
- **Next exact batch:** B2 (MCA supplementary-block parity + Burt)
- **Active PR:** [#5](https://github.com/aigorahub/FactoMinePy/pull/5)
- **Collision tripwire (latest own HEAD):** `d00e6cd` (staging tripwire was `19c448b`)
- **Test baseline:** 123→187 passed, 2 skipped (+64 parity tests; skips unchanged)

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

## Batch B2 — MCA sup-block parity + Burt — 2026-05-31 (IN PROGRESS: code done, awaiting CI fixture)

**Phase:** Implement complete; local green; rpy2-parity CI loop pending.
**Rollback tag:** `elves/pre-batch-b2` (pushed).

**Contract:** (1) implement MCA `quanti.sup` + `quali.sup` blocks (run #1 shipped the args but never
computed/asserted the blocks); (2) implement the `method="Burt"` transform.
- **quanti.sup:** weighted correlation of each sup numeric var with the individual coords (R uses
  svd$U; correlation is scale-invariant). coord only.
- **quali.sup:** route the sup categories through CA as `col.sup` (R does `CA(Ztot, col.sup=...)`);
  coord/cos2 = CA col.sup (principal CA col coord, **NO /√λ rescale** — the L1 trap); v.test = coord ×
  same multiplier as active categories; eta² = per-var weighted correlation ratio of ind coords.
- **Burt:** post-transform of the indicator decomposition — eig = λ_ind², var coord = ψ·√λ_ind, cos2
  vs the all-axes Burt distance (auxil); ind/contrib/eta² unchanged (MCA.R:226-234,253-256,329-333).

**Build on:** CA's `col_sup` block (coord/cos2) + `svd.U`; the active v.test multiplier; the shared
`weighted_corr`/`weighted_eta2` (the latter relocated from famd.py to `_corr.py` this batch — both
methods now share it; FAMD still 26/26). Active MCA path unchanged when no sup / indicator.

**Scope:** Burt is implemented for the all-active case; `method="burt"` + `quali_sup` raises a clear
NotImplementedError (not yet combined). quanti.sup under Burt is fine (ind unchanged).

**Local checks (pre-CI):** ruff clean; sphinx -W; pytest 192 passed / 6 skipped. Smoke: MCA sup blocks
(quanti_sup=age, quali_sup 44 cats/17 vars, eta² ∈ [0,1]); Burt eig == indicator eig² (exact), ind
unchanged, var coords = indicator × √λ_ind (exact).

**Fixtures (license-clean, tea):** extended `dump_mca` (NULL sup blocks drop out → active checks
unchanged); regenerate `mca/tea.json` (gains quanti.sup/quali.sup) + new `mca/tea_burt.json` (8-var
all-active Burt slice).

**Next:** push → trigger CI → verify the sup + Burt tests vs fresh R → commit fixtures → confirm
zero drift on the active tea.json data.

---

## Batch B1 — FAMD supplementary variables — 2026-05-31 (COMPLETE — 26/26 parity vs live R)

**Phase:** Implement → Validate → Review → Document, done. Parity-verified, first pass.
**Rollback tag:** `elves/pre-batch-b1` (pushed).
**Commits:** `f4dce2e` (impl + harness), `d00e6cd` (R fixtures + refreshed poison.json).

**Validation (final):** ruff clean; sphinx -W; pytest **187 passed / 2 skipped** (back to the 2-skip
baseline). CI green on both jobs, first attempt: the 18 active FAMD channels + 8 sup channels
(quanti.sup coord/cos2, quali.sup coord/v.test/eta2, var.coord.sup) all match live R. The sup-quali
barycenter routing (the flagged trap) and v.test matched R immediately.

**Regression attestation:** `famd.py` sup handling is gated on `sup_var` (None path = prior code,
active FAMD parity preserved — 18/18). `_result.py` adds two optional `Block` fields
(coord_sup/cos2_sup, default None). The refreshed `poison.json` gained four empty `{}` sup keys but
the active numeric data is byte-identical (eig diff 0.0). Test baseline 179→187 passed, skips 2→2.
**Confidence: HIGH** — sup vars reuse the parity-verified PCA sup blocks; active path untouched.
ind_sup deferred to B4 (recorded; raises NotImplementedError).

**Docs updated:** README (FAMD sup vars ✅), ROADMAP, CHANGELOG.

**Next:** confirm zero-drift CI, then B2 (MCA supplementary-block parity + Burt — assert MCA's
quanti.sup/quali.sup blocks that run #1 shipped but never asserted; verify method="burt").

**Contract:** add `sup_var` to `factominer/famd.py` — supplementary quantitative + qualitative
variables, routed through the inner PCA's `quanti_sup` / `quali_sup` (R FAMD does the same). sup-quanti
pre-scaled like active quanti (center + pop sd) → PCA quanti.sup correlations; sup-quali appended as
RAW factor → PCA quali.sup barycenters (coord/cos2/v.test/eta2) — NO active-quali transform (the trap).
Adds `var$coord.sup`/`cos2.sup` (sq loadings + eta²; FAMD.R:176-184) via new `Block.coord_sup`/`cos2_sup`.

**Scope decision:** `ind_sup` (supplementary individuals) DEFERRED to B4 (missing values + row
weights) — it needs active-only row weighting threaded through every FAMD scaling formula
(q_center/q_sd/prop/bary/eta2/vtest), a delicate change to parity-verified code best done alongside
B4's row-weight work. `FAMD(..., ind_sup=...)` raises a clear NotImplementedError pointing there.

**Build on:** PCA's existing `quanti_sup`/`quali_sup` blocks (already parity-verified). The active
FAMD path is UNCHANGED when `sup_var=None` (column partition reduces to all-active) — active FAMD
regression stays 18/18 green.

**Local checks (pre-CI):** ruff clean; sphinx -W; pytest 179 passed / 10 skipped (8 FAMD-sup tests
await the fixture). Smoke: `FAMD(poison, sup_var=["Time","Sex"])` → active quanti=Age, quanti_sup=Time,
quali_sup=Sex categories, var.coord_sup=[Time,Sex].

**Fixture (license-clean):** `FAMD(poison, sup.var=c("Time","Sex"))` — already-bundled poison.
Extended `dump_famd` (NULL sup blocks drop out, so the active `poison.json` stays byte-identical);
new `famd/poison_sup.json`.

**Hardest parity point:** sup-quali v.test (PCA barycenter form vs FAMD raw-coord form — algebraically
equal, verify numerically) and the bare-vs-prefixed category labels (test normalizes by suffix).

**Next:** push → trigger CI → verify the 8 FAMD-sup tests vs fresh R + confirm the active poison.json
is unchanged (zero drift) → commit fixture.

---

## Batch A4 — DMFA — 2026-05-31 (COMPLETE — 15/15 parity vs live R; PHASE A DONE)

**Phase:** Implement → Validate → Review → Document, done. Parity-verified. **MFA family complete.**
**Rollback tag:** `elves/pre-batch-a4` (pushed).
**Commits:** `9b68da1` (impl + harness), `5066e0e` (R fixture + named-list test fix).

**Validation (final):** ruff clean; sphinx -W; pytest **179 passed / 2 skipped** (back to the 2-skip
baseline). CI: all DMFA channels matched live R FactoMineR 2.14 — eig, svd, ind (reordered), var
(10 events), quanti.sup (Rank/Points), group (coord/coord.n/cos2 — the trace block), cor.dim.gr,
var.partiel. First CI round: 13/15 passed; the 2 failures were a TEST bug (R's named-list
`cor.dim.gr`/`var.partiel` serialize as objects keyed by level, not arrays — accessed by integer
index). Every DMFA *computation* matched R first time. No tolerance loosened; no fixture hand-edited.

**Regression attestation:** new `factominer/dmfa.py`, `tests/test_dmfa.py`, `dmfa/decathlon.json`;
`__init__.py` swaps the DMFA stub import for the real module; additive `refresh_r_fixtures.R` /
`conftest.py` / `test_smoke.py`. No existing method changed. Test baseline 164→179 passed, skips 2→2.
**Confidence: HIGH** — DMFA reuses the parity-verified PCA engine; only the per-group trace block is
new, and it matched R immediately.

**Docs updated:** README (DMFA ✅/✅, status prose, stub note removed — no methods remain stubbed),
ROADMAP, CHANGELOG.

**Next:** confirm zero-drift CI, run the **entropy check** (Phase A done — consolidate the three
correlation helpers across mfa/hmfa/dmfa), then Phase B / B1 (FAMD supplementary variables — research
spec captured: route through PCA's quanti_sup/quali_sup/ind_sup; compute active scaling from active
rows only; fixture `FAMD(poison, sup.var=c("Time","Sex"), ind.sup=c(1,2))`).

---

## Batch A3 — HMFA — 2026-05-31 (COMPLETE — 14/14 parity vs live R, first pass)

**Phase:** Implement → Validate → Review → Document, done. Parity-verified, no iteration.
**Rollback tag:** `elves/pre-batch-a3` (pushed).
**Commits:** `71b0212` (impl + MFA extension + harness), `d0cf12d` (R fixtures).

**Validation (final):** ruff clean; sphinx -W builds; pytest **164 passed / 2 skipped** (back to
the 2-skip baseline — all 14 HMFA tests run and pass). CI run 26732009122 **green on both jobs,
first attempt** — every channel matched live R FactoMineR 2.14 with zero fixes: eig, ind
(coord/cos2/contrib/dist), quanti.var (coord/cor/cos2/contrib), quali.var (coord/contrib),
group.coord (per hierarchy level), group.canonical. Two fixtures: poison categorical hierarchy +
decathlon pure-quanti sanity.

**Self-review:** the keystone `hweight` per-level `1/λ₁` accumulation is implicitly validated by
the clean eig/group$coord parity — and by the invariant that the top-level group coords sum to the
eigenvalue per axis (L2 Dim.1 = 1.8799 = eig₁). The MFA `weight_col_mfa` extension kept MFA's 27
channels unchanged (regression green).

**Regression attestation:** new `factominer/hmfa.py`, `tests/test_hmfa.py`, `hmfa/*.json`; additive
edits to `mfa.py` (new optional `weight_col_mfa` defaulting to ones → identical behavior; additive
call-dict keys), `__init__.py`/`_deferred.py` (HMFA stub→live), `refresh_r_fixtures.R`,
`conftest.py`, `test_smoke.py`. No product changed outside MFA-family scope; MFA's 27 + the rest of
the suite stay green. Test baseline 150→164 passed, skips 2→2. **Confidence: HIGH** — first-pass
parity on a complex method via maximal reuse of the already-verified MFA/PCA engines.

**Contract:** `factominer/hmfa.py` implements Hierarchical MFA on the MFA primitives. `H` =
list of per-level group counts (`H[0]` elementary sizes, `H[h≥1]` #prev-level groups per node);
types `s`/`c`/`n`. Outputs: `eig`, `ind` (coord/cos2/contrib/dist), `quanti.var`
(coord/cor/cos2/contrib), `quali.var` (coord/contrib), `group.coord` (LIST per hierarchy level),
`group.canonical`, `partial` (per-level arrays, plotting-tier).

**Build on / prerequisite (DONE):** extended `mfa.py` to accept `weight_col_mfa` (threaded into the
separate quantitative analyses) and to expose `call["XTDC"]` / `["col_w"]` / `["group_mod"]`. MFA
regression green (27/27). HMFA's `hweight` re-enters MFA per level passing `weight.col.mfa` and
multiplies in one `1/λ₁` per level (HMFA.R L41-56). New helpers `_htabdes`/`_hdil`/`_hweight`;
new `HMFAResult` container (group$coord is a list-per-level, so it can't reuse MFAGroup).

**Source-verified (HMFA.R):** hweight L41-56 (keystone accumulation `cw = niv2.col_w * cw`); the
final `PCA(XTDC, col.w=poids[top], scale_unit=False)` L101; group$coord L104-124 (`Σ var.coord²·
poids[h]` per node, level-h weights); partial coords L130-148; canonical L160-172 (unweighted
`diag(cor(ind, partial))`); quali.var barycenter L188-197.

**Local checks (pre-CI):** ruff clean; sphinx -W builds; pytest 151 passed / 15 skipped (13 HMFA
parity tests await the fixture). **Top-level group$coord sums to the eigenvalue per axis**
(L2 Dim.1 = 1.8799 = eig₁) — the HMFA analogue of MFA's group invariant.

**Fixtures (license-clean):** poison `H=[[2,2,5,6],[2,2]]` type `[s,n,n,n]` (categorical-heavy) +
decathlon[:,1:10] `H=[[4,3,3],[1,2]]` all `s` (pure-quanti sanity). New `dump_hmfa`.

**Deferred (recorded):** `quali.var$partial`, `ind$within.inertia`, the full `partial`-array dump
(validated indirectly via `canonical`), DMFA stays stubbed.

**Docs updated:** README (HMFA ✅/✅, status prose, stub note → DMFA), ROADMAP, CHANGELOG, learnings
L16–L17.

**Next:** confirm zero-drift CI, then A4 (DMFA — last Phase-A method). DMFA spec captured (per-group
standardized PCA + `group$coord = v_sᵀ Cov_j v_s / λ_s`; decathlon/Competition fixture). Note DMFA
does NOT use MFA's `1/λ₁` weighting (see [[L16]]).

---

## Batch A2 — MFA completeness — 2026-05-31 (COMPLETE — 27/27 parity vs live R)

**Phase:** Implement → Validate → Review → Document, done. Parity-verified.
**Rollback tag:** `elves/pre-batch-a2` (pushed).
**Commits:** `0e5aaae` (impl + harness), `b69e136` (extended R fixture + 2-D sign-align fix).

**Validation (final):** ruff clean; pytest **150 passed / 2 skipped** (27 MFA tests now, +6 over A1).
All 6 A2 channels match live R FactoMineR 2.14 at the bar: ind.coord.partiel (coord 1e-9),
group.correlation (1e-9), partial.axes coord/cor (1e-9, 2-D sign-aligned) + contrib (1e-8),
inertia.ratio (1e-9). First CI round: inertia.ratio/coord.partiel/group.correlation/contrib passed;
partial.axes coord/cor failed on a pure per-row sign flip (symptom group's 5th separate-MCA axis) —
magnitudes were exact (ratios precisely ±1), fixed with a row+column `_align_2d` (learnings L5). No
tolerance loosened; no fixture hand-edited.

**Self-review / internal cross-checks:** the barycenter invariant (mean over groups of partial coords
== global coord, 7e-15) independently confirms coord.partiel; partial.axes contrib sums to 100 per
axis; coord==cor for partial.axes (unit-variance tab); inertia.ratio ∈ (0,1].

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

**Regression attestation:** cumulative diff adds only `factominer/mfa.py` (A2 block), `_result.py`
(additive: `Block.coord_partiel`, `Result.partial_axes`, `Result.inertia_ratio`, `MFAGroup.correlation`
already optional), `refresh_r_fixtures.R` (extended dump), `tests/test_mfa.py`, and the regenerated
`mfa/poison.json`. No product files changed outside MFA scope; A1's 21 channels unchanged (still green).
Test baseline 144→150 passed, skips 2→2 (no test disabled). **Confidence: HIGH** — every channel exact
vs live R, the barycenter invariant holds, and the only deviation was an arbitrary SVD sign handled the
same way as every other coord channel.

**Docs updated:** README MFA row, ROADMAP, CHANGELOG [Unreleased].

**Next:** confirm zero-drift CI green, then A3 (HMFA). Note: A3 requires extending `mfa.py` to accept
`weight_col_mfa` and expose `call["XTDC"]`/`["col_w"]`/`["group_mod"]` (HMFA re-enters MFA per
hierarchy level with `weight.col.mfa`). Research spec captured for A3.

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
