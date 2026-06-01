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

- **Last updated:** 2026-06-01 (D2 regression family complete, parity-verified)
- **Current phase:** Phase A + B + C done; Phase D — D1 + D2 done, D3 (textual) next
- **Active batch:** D2 → done; next D3 (textual). B4b + meansComp deferred.
- **Last completed batch:** D2 (LinearModel/AovSum + RegBest) — contr.sum Type-III ANOVA + best-subset, parity vs live R
- **Next exact batch:** D3 (textual — free text → document×word contingency table)
- **Active PR:** [#5](https://github.com/aigorahub/FactoMinePy/pull/5)
- **Collision tripwire (latest own HEAD):** `56a1e39` (staging tripwire was `19c448b`)
- **Test baseline:** 123→231 passed, 2 skipped (+108 parity tests; skips unchanged)

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

## Batch D2 — regression family — 2026-06-01 (COMPLETE — parity vs live R, first CI try)

**Phase:** Complete. rpy2-parity CI green (run 26737903399); fixtures + zero drift.
**Rollback tag:** `elves/pre-batch-d2` (pushed).

**Contract:** `LinearModel` + `AovSum` (D2a) and `RegBest` (D2b). `meansComp` **deferred** (needs
`emmeans`/`multcompView` semantics — out of proportion to an EDA port). **No statsmodels added**
(numpy/scipy only; its defaults wouldn't match R's contr.sum layout anyway).

**D2a — `LinearModel`/`AovSum` (`factominer/linear_model.py`), verbatim from R LinearModel.R:**
contr.sum (sum-to-zero) OLS via `lstsq`. `Ftest` = Type-III/II SS (RSS increase from dropping a
term's columns) + `Residuals` row. `Ttest` = coefficient table rebuilt per factor level (k-1
contrasts + the omitted level = `-sum`, SE from the vcov submatrix; factor×factor interactions
reconstruct the full cell grid). `lmResult`: r.squared/sigma/fstatistic + aic/bic via R's
`extractAIC` (`n·log(RSS/n)+k·edf`, NOT loglik AIC). Stepwise `selection` + Type-II deferred. **All
matched R first try** ([[L24]]).

**D2b — `RegBest` (`factominer/reg_best.py`):** best subset per size by RSS (R's `leaps` ≡ exhaustive
`itertools.combinations` for small p), choose by `r2`/`Cp`/`adjr2`. Returns per-size models +
R²/Pvalue summary + the chosen best. **Fixture trap:** R's RegBest builds formulas without
backticking → non-syntactic names (`100m`) break it; both sides `make.names` the columns. And
decathlon `Points` is near-deterministic (degenerate) → used `Rank` (r2/Cp pick 6 vars, adjr2 picks
7) ([[L24]]).

**Fixtures (license-clean, bundled):** `linear_model/poison_main` (Time~Sick+Sex+Nausea) +
`poison_inter` (Time~Sick*Sex), `aovsum/poison_main`, `regbest/decathlon_{r2,cp,adjr2}`.

**Checks:** ruff clean; **231 passed / 2 skipped**; rpy2-parity green; SS/coef/SE/t 1e-6, p 1e-5, df
exact, R²/sigma/AIC/BIC 1e-6.

**Regression attestation:** additive — new `linear_model.py`, `reg_best.py` + tests + exports. No
existing engine touched. **Confidence: HIGH.**

**Docs:** README (LinearModel/AovSum/RegBest rows), ROADMAP, CHANGELOG, learnings L24, survival guide
+ `.elves-session.json` advanced to D3.

**Deferred (recorded):** `meansComp`; LinearModel Type-II SS + aic/bic stepwise selection.

**Commits:** `9f3e094` (RegBest), `56a1e39` (LinearModel/AovSum + RegBest fixture fix), + close-out.

---

## Batch D1 — CaGalt (type s/c) — 2026-06-01 (COMPLETE — parity vs live R)

**Phase:** Complete. rpy2-parity CI green (run 26737273383); cagalt fixture + zero drift.
**Rollback tag:** `elves/pre-batch-d1` (pushed).

**Contract:** `CaGalt(Y, X, type, conf_ellip, nb_ellip, level_ventil, sx, ...)` — Correspondence
Analysis on Generalized Aggregated Lumped Tables; relates a frequency table `Y` to covariates `X`.
New `factominer/cagalt.py`; new `freq` Block slot on `Result`.

**Implementation (verbatim from R `CaGalt.R`, a thin orchestrator over PCA):** `P=Y/sum`,
`PI=rowSums`, `PJ=colSums`. `phi.stand` = PI-orthonormal covariate PC scores (direct PI-weighted SVD,
matching R's `svd.triplet` U). `L=(P'phi.stand)/PJ`, `T=P'Xc`, `C=Xc'diag(PI)Xc`, `W=(T pinv(C))/PJ`.
Inner `PCA(cbind(L,W), W sup, scale_unit=F, row_w=PJ)` → eig, freq (=inner ind), and the individual
coords by transition `coord.ind=(P@svd.U_unwhitened)/PI`, `cos2=coord/rowSS`.

**Two parity bugs found + fixed (first CI run; eig/ind/freq-coord matched immediately so the
whitening conversions were right):**
1. **Degenerate fixture data** — the old synthetic `Y` was linear in z, so the quadratic covariate's
   regression coefficient `W[:,cov3]` was exactly 0 → its `quanti.var` cor/cos2 was the correlation of
   `pinv` noise (R `ginv` vs numpy `pinv` diverge), and the inner 3rd eigenvalue was ~0 (freq.contrib
   Dim3 = 0/0). Redesigned `Y` to depend on all three latent factors → `W` well-conditioned, all
   inner eigenvalues non-zero ([[L23]]).
2. **`quanti.var$coord`** — the port's PCA `quanti_sup` conflates coord/cor when `scale_unit=False`
   (both = the correlation); R's coord is the covariance-projection. Computed `quanti.var` directly in
   `cagalt.py` (`coord = <Wc, U>_PJ`, `cor = coord/sd_PJ`, `cos2 = cor²`) — leaves FAMD's tested
   quanti_sup path untouched.

**Fixture (license-clean):** synthetic `cagalt_synth.csv` (12×[6 freq Y | 3 quanti X], MIT;
FactoMineR's `health` is GPL + 115 cols) + `load_cagalt_synth()` + PROVENANCE. `CaGalt(Y, X,
type="s")` → `cagalt/synth_s.json`.

**Checks:** ruff clean; **225 passed / 2 skipped**; rpy2-parity green; eig 1e-10, coord/cos2/cor 1e-9,
contrib 1e-8, all sign-aligned where needed.

**Regression attestation:** additive — new `cagalt.py`, new `freq` Result slot, new synthetic
dataset + loader. No existing engine touched. **Confidence: HIGH.**

**Docs updated:** README (CaGalt row), ROADMAP, CHANGELOG, learnings L23, survival guide +
`.elves-session.json` advanced to D2.

**Deferred (recorded):** CaGalt `type="n"` (qualitative covariates — needs a row-weighted MCA) and
`conf_ellip` bootstrap ellipses (stochastic); both raise `NotImplementedError`.

**Commits:** `1adc61b` (impl), `46faab4` (data + quanti.var fix), + this close-out.

---

## Batch C3 — descfreq — 2026-06-01 (COMPLETE — parity vs live R; PHASE C DONE)

**Phase:** Complete. rpy2-parity CI green; descfreq fixture generated + zero drift.
**Rollback tag:** `elves/pre-batch-c3` (pushed).

**Contract:** `descfreq(donnee, by_quali=NULL, proba=0.05)` — the CA analogue of `catdes`. For each
ROW of a frequency/contingency table, report the COLUMNS significantly over/under-represented vs the
marginals (two-sided hypergeometric), sorted by descending `v.test`.

**Implementation (verbatim from R `descfreq.R`, fetched via GitHub API):** new
`factominer/desc/descfreq.py`. Per cell `n_jk`: over (`n_jk/marge.col > marge.li/total`) →
`p=2·P(X≥n_jk)` via `hypergeom.sf(n_jk-1)`; else `p=2·P(X≤n_jk)` via `cdf(n_jk)`; `p>1→2-p`. Keep if
`p<proba`; `v.test=(1-2·[over])·qnorm(p/2)`; row stats `[Intern %, glob %, Intern freq, Glob freq ,
p.value, v.test]` (the "Glob freq " column name carries R's trailing space). Reuses the scipy
`hypergeom` + `±qnorm(p/2)` machinery from `catdes` — but the **plain** `phyper×2` test, NOT catdes's
mid-p (kept distinct).

**Fixture (license-clean):** `descfreq(children[1:14, 1:5])` → `descfreq/children.json` (6 of 14 rows
have significant columns). Added `dump_descfreq` to the R dump.

**Checks:** ruff clean; **221 passed / 2 skipped**; rpy2-parity green; p.value 1e-5 rel, v.test 1e-6,
%/freq columns 1e-9; the significant-column set per row matches R exactly.

**Also this batch — a flaky GPA test fixed (commit `0b51a00`):** the `r-fixture-drift` artifact
proved R's GPA is NOT reproducible across CI runs even with `set.seed` (consensus/Xfin reflection
flips; PANOVA SS drifts ~2e-4 run-to-run). The PANOVA objet/config assertions were mis-tiered at
`atol=1e-4` (flaked ~half the runs) — corrected to the stochastic tier `atol=1e-3, rtol=1e-3`
([[L22]]). Not a deterministic-tolerance loosening; a tier correction. RV/RVs/simi stay exact;
consensus/Xfin stay pdist-compared.

**Regression attestation:** additive — new `descfreq.py` + test + export; the GPA change only
loosens a stochastic-tier test tolerance with documented justification. **Confidence: HIGH.**

**Docs updated:** README (descfreq row), ROADMAP (Phase C ✅), CHANGELOG, learnings L22, survival
guide + `.elves-session.json` advanced to D1.

**Commits:** `6c77eeb` (descfreq), `0b51a00` (GPA tier fix), + this close-out.

---

## Batch C2 — reconst + estim_ncp — 2026-06-01 (COMPLETE — parity vs live R)

**Phase:** Complete. rpy2-parity CI green (run 26736100357); 4 fixtures generated + zero drift.
**Rollback tag:** `elves/pre-batch-c2` (pushed).

**Contract:** `reconst(res, ncp)` — low-rank reconstruction of the active table from the first `ncp`
axes; `estim_ncp(X, ncp.min, ncp.max, scale, method)` — estimate the PCA component count by GCV /
smoothing. New `factominer/reconst.py`; both exported.

**Implementation (verbatim from R `reconst.R` / `estim_ncp.r`, fetched via the GitHub API):**
- **reconst PCA:** `hatX = coord.ind[,1:ncp] @ (coord.var[,1:ncp]/√eig)ᵀ`, then `× ecart.type`,
  `+ centre`. **CA:** chi-square reconstruction `sum(X)·(√Rr · S · √Rc + Rr·Rcᵀ)` with
  `S = (U√eig)Vᵀ`, `U = row.coord·√Rr/√eig`, `V = col.coord·√Rc/√eig` — needs only the stored
  `marge_row`/`marge_col`/`N` (not the original table). Full-rank reconstruction reproduces the
  active table to ~1e-14. **MFA reconst deferred** (needs per-group separate-analysis scales; only
  defined for all-quanti groups) — recorded.
- **estim_ncp:** plain SVD of the centred (+ optionally sd-scaled, ddof=1) table; incremental
  rank-q reconstructions; GCV criterion `mean((n·p·(X-rec)/((n-1)(p-pquali) - q(n+p-pquali-q-1)))²)`;
  Smooth criterion via the `(1-1/n-a)` / `(1-b)` leverage normalization. Chooses the **first local
  minimum** of the criterion (`which(diff(crit)>0)[1]`), not the global min ([[L21]]).

**Fixtures (license-clean):** `reconst/pca_decathlon` (PCA(decathlon[,1:10]), ncp=2),
`reconst/ca_children` (CA(children, sup), ncp=2), `estim_ncp/decathlon_gcv` +
`estim_ncp/decathlon_smooth` (ncp.max=6). Added `dump_reconst`/`dump_estim_ncp`.

**Checks:** ruff clean; **220 passed / 2 skipped**; rpy2-parity green; reconst entries match R to
1e-9, estim_ncp criterion to 1e-7 rel and the chosen `ncp` exactly (GCV→3, Smooth→2 on decathlon).

**Regression attestation:** additive — new `reconst.py`, new `test_reconst.py`, two new exports. No
existing code touched besides `__init__`. **Confidence: HIGH.**

**Docs updated:** README (reconst + estim_ncp rows), ROADMAP (C2 ✅), CHANGELOG, learnings L21,
survival guide + `.elves-session.json` advanced to C3.

**Commits:** `da48f88` (impl), + this close-out.

---

## Batch C1 — predict.* family — 2026-06-01 (COMPLETE — all four parity vs live R)

**Phase:** Complete. rpy2-parity CI green; 4 predict fixtures generated + committed.
**Rollback tag:** `elves/pre-batch-c1` (pushed).

**Contract:** `predict.PCA` / `predict.MCA` / `predict.FAMD` / `predict.MFA` — project new
(held-out) individuals onto a fitted model, returning `coord`, `cos2`, and the distance to the
origin. New `factominer.predict(res, newdata)` dispatches on `res.method`.

**Design — one shared projection, four scalings:** added `factominer/predict.py` with
`_project_scaled(M_scaled, col_w, V)` = `coord = (M·√col.w) @ svd$V`; `dist²` weighted; `cos²`.
PCA's `ind_sup` block now calls it too (centralize; removed a dead overwritten line). Per method the
only difference is how `M_scaled` is built from the **training** stats stashed on `call`:
- **PCA:** `(X-centre)/ecart.type`, `col.w` = active col weights. (`mean`/`scale`/`col_w` already stashed.)
- **MCA:** indicator row profile `(prof - marge.col)/√marge.col` via the CA transition formula,
  `col.w=1`; coord is the **principal** row coord (= `ind$coord` scale), not the standard `var$coord`.
  Stashed `marge_col` on the MCA call.
- **FAMD:** `[(Q-centre)/sd | (1[cat]-prop)/√prop]`, `col.w=1`. Stashed `q_center`/`q_sd`.
- **MFA:** per-group scaling (`group_meta`): quanti centre/scale by the group's training
  centre/ecart.type (`"c"` scales by 1); **categorical uses R's `(1[cat]-2·marge.col)/ec` form** —
  centred at `2p/J` (separate-MCA margin) with the weighted-RMS denominator, NOT the fit-time
  `(1[cat]-p)/√(p(1-p))`. No global-mean subtraction.

**The MFA subtlety (learnings [[L20]]):** the MFA active analysis is parity-exact, yet a naïve
"reuse the fit scaling" predict was ~7% off out-of-sample. R's `predict.MFA` uses a *different*
categorical parametrization than the fit; the two are covariance-equivalent after the global PCA
recentres, so they agree on the active fit but diverge for new rows. Caught it by fetching R's
`predict.MFA.R` and reconciling (the in-sample property `predict(train)==ind$coord` held for the
wrong version too — it can't catch this; held-out fixtures can).

**Fixtures (held-out splits, license-clean):** `predict_pca/decathlon` (fit 1:38, predict 39:41),
`predict_mca/tea` (fit rows 6:300, predict 1:5), `predict_famd/poison` + `predict_mfa/poison` (fit
6:55, predict 1:5). Splits chosen so held-out rows carry no unseen categories.

**Checks:** ruff clean; **216 passed / 2 skipped** locally; rpy2-parity green; all four predict
methods match live R at the supplementary tier (coord 1e-7 after per-axis sign alignment;
cos2/dist 1e-7). In-sample cross-check (predict(train) == `ind$coord`) exact for all four.

**Regression attestation:** additive — new `predict.py`; PCA `ind_sup` refactored onto the shared
helper (PCA/FAMD/MCA suites still green); MCA/FAMD/MFA gained `call`-dict stashes only. No product
code deleted; no test weakened. **Confidence: HIGH.**

**Docs updated:** README (predict row), ROADMAP (C1 ✅), CHANGELOG [Unreleased], learnings L20,
survival guide + `.elves-session.json` advanced to C2.

**Deferred (carry forward):** B4b (missing values + FAMD `ind_sup`); Burt + `quali_sup`.

**Commits:** `bfa74a8` (PCA/MCA/FAMD), `17dada0` (MFA + fixtures), + this close-out.

---

## Batch B5 — dimdesc CA/MCA — 2026-06-01 (COMPLETE — MCA parity vs live R; CA self-consistent)

**Phase:** Complete. rpy2-parity CI green (run 26734779119, both jobs success); zero drift confirmed.
**Rollback tag:** `elves/pre-batch-b5` (pushed).

**Contract:** wire `dimdesc` for CA and MCA results (previously only PCA; CA/MCA raised). Per R
`dimdesc.r` (49 lines): **MCA uses the SAME condes-based path as PCA** (`condes(ind.coord[,k], X)`
per axis) — so it's free once MCA's call carries the original data; **CA has its own branch** — per
axis, the sorted row + column coordinates (active + supplementary), each a one-column `coord` frame.

**Build on:** added `active_frame` to MCA's call dict → dimdesc(MCA) routes through the existing
parity-verified condes path. New `_dimdesc_ca` helper for the CA branch. No change to the PCA path.

**Two R 2.14 quirks surfaced and handled (both faithfully, no test/fixture fudging):**
1. **`dimdesc(CA)` is broken on R 4.x.** FactoMineR 2.14's CA branch does
   `order(tableau[, k, drop=FALSE])` on a 1-col data.frame → "cannot xtfrm data frames". So R
   produces NO usable CA fixture. The CA branch is a pure re-sort of the (already R-parity-verified)
   CA coordinates, so `test_dimdesc_ca_self_consistent` verifies it directly against
   `res.row.coord`/`res.col.coord` sorted ascending (active + sup), not against an R dump. The R dump
   for CA dimdesc was removed from `refresh_r_fixtures.R`.
2. **`dimdesc(MCA)` attaches a `call` element.** R's `else` branch sets `result$call <- result[[1]]$call`,
   so `names(dimdesc(MCA))` = `["Dim 1", "Dim 2", "call"]`. The test's per-axis loop now parses the axis
   index from the `"Dim N"` key and skips `call`; the R dump skips the `call` element too so regenerated
   fixtures stay clean (`["Dim 1", "Dim 2"]`).

**Result schema (MCA, per axis):** `quali` (R² + p.value, sign-invariant) and `category` (Estimate
sign-dependent + p.value). Test asserts quali R²/p.value to 1e-7/1e-6; category count + sorted
p.value set (Estimate signs ambiguous across colliding category labels → count+pvalue match).

**Fixtures (license-clean):** `dimdesc(MCA(tea[,1:6], ncp=5))` → `dimdesc/mca_tea.json` (CA fixture
intentionally absent — see quirk 1). Generated + zero-drift confirmed via the CI loop.

**Local + CI checks:** ruff clean; pytest **212 passed / 2 skipped** locally; rpy2-parity job green
against fresh live-R fixtures; fresh-vs-committed diff = only the expected `call`-removal on
`mca_tea.json`, every other committed fixture byte-identical.

**Regression attestation:** additive — new `_dimdesc_ca` branch in `desc/dimdesc.py`, MCA `call` now
carries `active_frame` (`mca.py`), new `tests/test_dimdesc_camca.py`. PCA dimdesc path untouched and
still green. No product code deleted; no test weakened. **Confidence: HIGH.**

**Docs updated:** ROADMAP (dimdesc CA/MCA ✅), CHANGELOG [Unreleased], learnings (L16–L18 + the two
R-2.14 dimdesc quirks), survival guide + `.elves-session.json` advanced to C1.

**Deferred (recorded, not dropped):** B4b = missing-value handling (PCA/CA/MCA/GPA) + FAMD `ind_sup`;
Burt + `quali_sup` combination. Slot into the long tail.

**Commits:** `06e3559` (test/dump fix + fixture), + this close-out commit.

---

## Batch B4 — row weights (PCA row.w) — 2026-05-31 (COMPLETE — 24/24 PCA parity vs live R)

**Phase:** Implement → Validate → Review → Document, done. Parity-verified, first pass.
**Rollback tag:** `elves/pre-batch-b4` (pushed).
**Commits:** `674c19b` (fix + harness), `88786d9` (R fixture).
**Validation (final):** ruff clean; pytest **209 passed / 2 skipped** (baseline). CI green both jobs,
first attempt: the 4 row.w channels (eig/var.coord/ind.coord/ind.contrib) match live R; existing PCA
fixtures byte-identical (eig diff 0.0). **Confidence: HIGH** — the normalization is a no-op for the
uniform default and every existing caller; only non-uniform `row_w` changes, now matching R.
**Docs updated:** CHANGELOG (Fixed: PCA row.w), ROADMAP.

**Scope decision — B4 split.** The plan's B4 ("missing values + row weights") is large and spans
several methods with DIFFERENT NA semantics. This batch (B4) does the **row-weights** half — the
clean, bounded, high-value piece — and defers the missing-value handling to **B4b** (recorded below).

**Contract (B4):** fix and parity-verify PCA's `row_w`. **Bug found:** the port's PCA did NOT
normalize `row_w` (it used the raw weights in the SVD, so `row_w=ones` gave eigenvalues n× too big);
R normalizes `row.w/sum(row.w)` (PCA.R). Fixed: normalize `active_row_w` to a probability vector.
All current callers (FAMD/MFA/HMFA/DMFA) pass uniform/None, so they are unaffected (full suite 205
passed — no regression; `row_w=ones` now matches the default exactly).

**Local checks (pre-CI):** ruff clean; pytest 205 passed / 6 skipped (4 PCA row.w tests await the
fixture). Smoke: non-uniform `row_w` runs; `row_w=ones == default`.

**Fixture (license-clean):** `PCA(decathlon[,1:10], row.w=rep(c(1,2,3), length.out=n))` →
`pca/decathlon_roww.json` (deterministic 1/2/3 weights). Tests assert eig/var.coord/ind.coord/contrib.

**B4b — DEFERRED (recorded for a later batch):** missing-value handling for PCA (iterative imputation
vs complete-case), MCA (NA→`.NA` category), and GPA (the VMQTE path); plus FAMD `ind_sup`
(supplementary individuals — needs active-only row weighting through the FAMD scaling). Specs captured
in the B1 (FAMD) and B3 (GPA) research summaries. R's NA semantics differ per method — verify each
before implementing.

**Next:** push → trigger CI → verify the 4 PCA row.w tests vs fresh R → commit fixture → confirm the
existing PCA fixtures are unchanged (the fix only affects non-uniform weights).

---

## Batch B3 — GPA edge cases — 2026-05-31 (COMPLETE — 16/16 GPA parity vs live R)

**Phase:** Implement → Validate → Review → Document, done. Parity-verified.
**Rollback tag:** `elves/pre-batch-b3` (pushed).
**Commits:** `66e03c9` (impl + harness), `93e9bfb` (R fixtures + symmetric simi fix).

**Validation (final):** ruff clean; sphinx -W; pytest **205 passed / 2 skipped** (back to baseline).
CI: unequal-width RV/RVs/simi (Tier-1 exact) + consensus/Xfin (Tier-2 pdist) + PANOVA objet/config
(Tier-1) all match live R; equal-width regression unchanged (7/7) + its new PANOVA assertions.

**First CI round** surfaced one issue: `simi(g1,g2)` (width-2 vs width-3 pair) was 0.985 vs R's 0.983
— `_similarite` rotated the WIDER config onto the narrower and under-counted the `trace(yᵀy)`
denominator. Fixed with the symmetric singular-value form `Σσ(XcᵀYc)/√(tr·tr)`, which equals the
prior formula for equal widths (no equal-width regression) and matches R for unequal widths.

**Regression attestation:** `gpa.py` `max(group)`/padding reduces to prior code for equal widths;
`_procrustes_H` k=min slice = U@Vt when square; new symmetric `_similarite` = prior for square. New
`GPAResult.panova` field (default {}). New synthetic `gpa_synth_uneven.csv` (provenance documented).
Test baseline 196→205 passed, skips 2→2. **Confidence: HIGH** — equal-width unchanged; unequal-width
exact on the Tier-1 invariants; the stochastic boundary (consensus/Xfin/correlations) stays Tier-2.

**Scope/deferred:** GPA **missing values** (VMQTE) → B4 (NaN still raises NotImplementedError → B4).

**Docs updated:** README (GPA unequal-width + PANOVA), ROADMAP, CHANGELOG.

**Next:** confirm zero-drift CI, then B4 (missing values + row weights — PCA/CA/MCA NA handling +
`row.w`; folds in GPA missing-values + FAMD `ind_sup` deferred from B3/B1).

**Contract:** (1) **unequal-width configurations** — lift the equal-width restriction in `gpa.py`
(pad each calibrated config to `max(group)`; `_procrustes_H` generalized to the semi-orthogonal map
for the unequal-width `similarite`); `invgC=C/K` stays exact with no NAs. (2) Add **`correlations`**
(per-config `group[i]` original vars vs consensus; `averagecor` only when equal-width) and **PANOVA**
(the sansvm objet/config/dimension SS tables, percent-of-total).

**Scope decision:** GPA **missing values** (the VMQTE path) DEFERRED to B4 (missing values + row
weights) — it needs `M`/`Cj` 0/1-diagonal metrics, `invgC=pinv(Cc)≠C/K`, and pairwise-deleted RV/simi,
which belong with B4's missing-value work. The NaN NotImplementedError stays for now (points to B4).

**Build on:** the existing deterministic single-start `algogpa` core (unchanged for shape) + the
two-tier parity (RV/RVs/simi exact; consensus/Xfin rotation-invariant via pdist). PANOVA objet/config
tables sum over consensus dims → rotation-invariant → Tier-1; the per-dimension table is Tier-2.

**Local checks (pre-CI):** ruff clean; sphinx -W; pytest 198 passed / 9 skipped. Equal-width GPA
regression unchanged (7/7). Unequal-width smoke: consensus width 3, RV symmetric/diag-1, simi diag~1,
PANOVA SStotal sums to exactly 100%.

**Fixtures (license-clean, synthetic):** new frozen `gpa_synth_uneven.csv` (`group=[2,3,2]`, derived
deterministically from `gpa_synth.csv`); extended the GPA dump with correlations + PANOVA; new
`gpa/synth_uneven.json`. Provenance documented.

**Hardest parity point:** the `procrustesbis` rank-deficient branch is stochastic in R (rnorm basis
completion) → unequal-width consensus/Xfin stay Tier-2; RV/RVs/simi + PANOVA objet/config totals are
the exact (Tier-1) assertions.

**Next:** push → trigger CI → verify the GPA edge-case tests vs fresh R → commit fixtures → confirm
the equal-width synth.json active data is unchanged.

---

## Batch B2 — MCA sup-block parity + Burt — 2026-05-31 (COMPLETE — 20/20 MCA parity vs live R)

**Phase:** Implement → Validate → Review → Document, done. Parity-verified, first pass.
**Rollback tag:** `elves/pre-batch-b2` (pushed).
**Commits:** `901f411` (impl + harness), `0d61192` (R fixtures + refreshed tea.json).

**Validation (final):** ruff clean; sphinx -W; pytest **196 passed / 2 skipped** (back to the 2-skip
baseline). CI green on both jobs, first attempt: the active MCA blocks + the new sup blocks
(quanti.sup coord; quali.sup coord/cos2/v.test/eta2) + the Burt blocks (eig/var coord/cos2, ind) all
match live R. The L1 standard-coord trap was handled correctly (quali.sup coord = CA col.sup, no
/√λ); Burt eig = indicator eig² exact.

**Regression attestation:** `mca.py` sup/Burt code gated on the sup args / method (indicator-no-sup =
prior code; active MCA unchanged). `_corr.py` gained `weighted_eta2` (relocated from famd.py — identical
math; FAMD still 26/26). The refreshed `tea.json` gained quanti.sup/quali.sup keys but the active
numeric data is byte-identical (eig diff 0.0). Test baseline 187→196 passed, skips 2→2.
**Confidence: HIGH** — sup blocks reuse the parity-verified CA col.sup + the active v.test multiplier;
Burt is a verified post-transform.

**Scope/deferred:** Burt + `quali_sup` raises NotImplementedError (not yet combined — recorded).

**Docs updated:** README (MCA sup + Burt ✅), ROADMAP, CHANGELOG, learnings L18.

**Next:** confirm zero-drift CI, then B3 (GPA edge cases — missing values / unequal-width configs;
assert correlations + PANOVA).

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
