# Project Learnings — FactoMinePy

> Durable memory across elves runs. Stable, reusable lessons the agent
> should not have to rediscover: repo conventions, tooling quirks,
> flaky tests, review heuristics, R FactoMineR-specific traps.
>
> Read this after the survival guide and `.elves-session.json`, before
> the plan and execution log. Promote new lessons here when they will
> matter again. Promote into `.ai-docs/*` when they become stable repo
> truths.

---

## Promotion Rules

Promote if: **reusable** (likely to help another batch or run),
**stable** (won't change in the next hour), **actionable** (changes what
to do, avoid, or verify), and **specific** (concrete enough to apply
without guessing).

Retire by moving to `## Retired Learnings` with a one-line note about
what changed — don't silently delete.

---

## Carry-overs from the previous round (FactoMineR 2.14 parity pass)

### L1 — MCA's `var$coord` is the **standard** category coordinate, not principal

**Context:** R FactoMineR's MCA `var$coord` ≠ the principal MCA category
coord `G_c`. The relationship is `G_c = ψ_c * sqrt(lambda_k)` where
`ψ_c` is the standard coord. R FactoMineR stores `ψ_c` in `var$coord`
(not `G_c`).

**Consequence:** in MCA,
- `eta²(v, k) = sum_c n_c * ψ_c² / N` (no `/lambda_k`)
- `v.test(c, k) = ψ_c * sqrt(n_c * (N-1) / (N - n_c))` (no `/sqrt(lambda_k)`)

**Why it matters here:** FAMD shares the indicator-block scaling pattern
with MCA. Before implementing FAMD, **read FactoMineR's FAMD.R source
carefully** and verify which convention `var$coord` uses for the
quali-half columns. If it's the standard coord, the same formula
adjustments apply. If it's principal, the formulas are different. Don't
guess from MCA's convention.

**Reference:** `husson/FactoMineR/R/MCA.R` lines 270 (quali.sup scaling
flag), 278–280 (v.test), 282–302 (eta² aggregation).

### L2 — R FactoMineR's `res$eig` carries the full rank, not `ncp`

**Context:** PCA, CA, MCA all return all eigenvalues in `res$eig` (full
rank), not just `ncp`. Only the coord/cos²/contrib blocks are truncated
to `ncp`. MCA specifically truncates to `total_cat - q_vars` because
the trailing `q_vars - 1` eigenvalues are spurious dummy-coding
artifacts.

**Why it matters here:** FAMD's eigenvalue handling needs the same
"full eig table, truncated coord blocks" pattern. Check whether FAMD
also has a spurious-eigenvalue truncation (it should, since it inherits
the indicator-method structure).

### L3 — Tests must assert every R-emitted column, not just numeric tolerances

**Context:** Previous round shipped 83 parity tests asserting every
column of every R output channel individually. A column-by-column
assertion catches schema regressions (R 2.10+ added the `n` column to
dimdesc/condes/catdes quanti tables; we initially missed it).

**Why it matters here:** every new batch must include a complete
column-by-column test, not just "eigenvalues match". Use
`tests/test_pca.py` and `tests/test_mca.py` as the structural template
— one assertion per R-emitted column with the tolerance bar from
ROADMAP.md.

### L4 — R fixtures must be regenerated on-CI; R is not installed locally

**Context:** macOS dev machine has no R. The `rpy2-parity` CI workflow
installs R 4.6 + FactoMineR 2.14 + jsonlite from CRAN, runs the R
script, and uploads the fresh JSON as `r-outputs-fresh.tar.gz`. The
loop is documented in the survival guide under "R access loop".

**Why it matters here:** every batch that adds an R fixture goes
through this loop. Don't try to install R locally — the build deps are
large and the install is non-trivial. The CI loop is faster
end-to-end than a local install would be.

### L5 — Sign of axes is arbitrary; align before comparing coords

**Context:** SVD is sign-ambiguous. R FactoMineR and our port may
choose opposite signs for a given axis. `factominer._sign.align_to_reference`
flips signs so coords match a reference matrix. Apply it before any
`np.allclose` comparison of coord-like quantities.

**Sign-invariant quantities** (no align needed): cos², contrib, eta²,
dist, inertia, eigenvalues, p-values, R² / Eta² in desc tables.

**Sign-dependent quantities** (align before compare): coord, cor,
v.test (sign tracks coord sign).

### L6 — `catdes`'s `quanti.var` uses `P-value` (capital P, hyphen), the rest use `p.value`

**Context:** FactoMineR has inconsistent column naming across functions.
`catdes()$quanti.var` columns are `Eta2` and `P-value`. Every other
desc table uses `p.value` (lowercase, dot). This is an R quirk, not a
bug — match it exactly.

**Why it matters here:** for any new desc table emitted by FAMD or GPA
(e.g. FAMD's `quanti.var` if FactoMineR exposes one), check R's exact
column name before naming yours.

### L7 — Commit message + commit body is the channel to the reviewer

**Context:** The PR review subagent reads the commit history before
flagging. When a value is hardcoded with a clear justification in the
commit body, the reviewer recognizes it as intentional. Without that
justification, the reviewer flags it as a violation and you burn a
review cycle.

**Why it matters here:** every hardcoded constant, every formula
choice that isn't obvious, every deviation from a pattern in the
codebase — explain in the commit body. The format is
`[<branch> · Batch N/Total] <verb> <what>`, body explains why.

---

## Batch 1 (FAMD) lessons

### L8 — FAMD truncates `res$eig` to `ncp` (opposite of PCA/CA/MCA)

FAMD.R:126 does `eig <- pca$eig[1:ncp,]`. Unlike PCA/CA/MCA (which return
the full eigenvalue spectrum), FAMD returns exactly `ncp` rows. The
spurious indicator-coding axes are removed by the ncp cap
`min(ncp, n-1, n_quanti + n_cat - n_factors)` (FAMD.R:123) — the
`- n_factors` is FAMD's analogue of MCA's `total_cat - q_vars`.

### L9 — FAMD `quali.var$coord` is the PRINCIPAL coordinate (NOT the MCA standard coord)

FAMD.R:154: `coord = pca_var_coord[dummy] / sqrt(prop) * sqrt(eig)`. This
is the category barycenter on the same scale as `ind$coord` (overlay-able
on one map). Contrast L1 (MCA stores the *standard* coord ψ_c). But
`quali.var$v.test` (FAMD.R:157) uses the **raw** `pca$var$coord` of the
dummy, not the transformed coord — easy to conflate.

### L10 — FAMD = `PCA(X, scale.unit=FALSE, col.w=1)` on a pre-scaled mixed matrix

The whole method delegates to PCA (FAMD.R:124). Quanti columns are
standardized (population sd, `ec.tab` rule: sd≤1e-16 → 1); each indicator
column is centered by its proportion and divided by `sqrt(prop)`. No
per-column weight beyond that — `col.w=1` for every column. Our `PCA`
accepts `scale_unit=False` + `row_w`, so the port is a wrapper, not a
re-implementation of the SVD. This pattern (build scaled matrix → call
PCA → post-process blocks) is the template for MFA in run #2.

### L11 — jsonlite drops integer "1..N" rownames as "automatic"

When an R data.frame has rownames `"1".."55"` (e.g. poison read with
`row.names=1`), jsonlite omits the `_row` key entirely. The `ind` block
fixture rows then have no label. Compare such blocks **positionally**
(R emits rows in input order = our `res.ind.coord` order), exactly as the
MCA tea ind block does. Datasets with real string rownames (decathlon,
children) don't hit this.

## Batch A1 (MFA) lessons

### L12 — MFA = a weighted PCA on the 1/λ₁-normalized concatenation; reuse `PCA` wholesale

The whole method delegates the eigen-step to `PCA(data, scale_unit=False,
col_w=ponderation, quali_sup=raw_factors)`, exactly as R delegates to
`FactoMineR::PCA`. So `ind`, `var`→`quanti.var`, `quali.sup`→`quali.var`
(coord/cos2/v.test), `eig`, `svd` all come from the already-parity-tested
engine. **Only three things are MFA-specific:** (1) the per-group `1/λ₁`
column weight (λ₁ = first *eigenvalue* of the group's separate PCA(`s`/`c`) /
MCA(`n`) — eigenvalue, not singular value); (2) the standardized-block
assembly; (3) the `group`/`Lg`/`RV` block. This "build scaled matrix → call
PCA → post-process" pattern (same as FAMD, [[L10 in the FAMD section]]) is the
template **HMFA and DMFA (A3/A4) will reuse** — they're built on MFA's
primitives, so keep the per-group normalization + global-PCA helpers factorable.

### L13 — A categorical MFA group enters as a *standardized* centered indicator, NOT FAMD's `1/√p`

For a `type="n"` group, each category column entering the global PCA is
`(1[i∈k] − p_k)/√(p_k(1−p_k))` (R `MFA.R` L262-269 nets to this), with column
weight `(1 − p_k)/(λ₁·J)` where `J` = #variables in the group (L261). Contrast
FAMD, which uses `(1[i∈k]−p)/√p` ([[L9]]). The two are algebraically equivalent
once the column weight is folded in, but R splits it the `√(p(1−p))` / `(1−p)`
way and you must reproduce the split exactly for byte-parity. Easy bugs:
dropping the `/J` factor, or using `1/√λ₁` instead of `1/λ₁`.

### L14 — `group$coord` = contribution-fraction × eigenvalue; `dist2`/`cos2` use two different denominators

`group$coord[g,k] = (Σ of group g's column contributions on axis k, as a [0,1]
fraction) × eigenvalue_k`. **Strong self-check: the group coords sum to the
eigenvalue down each axis** (Σ_g coord[g,k] = λ_k). Reported `group$contrib` is
that fraction ×100. `group$dist2 = diag(Lg)` (the `funcLg` self-link), but
`group$cos2` uses the *separate-spectrum* `Σ(λ_l/λ₁)²` denominator (R computes
cos2 at L417 before overwriting dist2 with diag(Lg) at L450 — the two are
numerically equal). The `Lg`/`RV` "MFA" row/col divides by the **global** first
eigenvalue `res.globale$eig[1,1]`, not any group's λ₁.

### L15 — `dump_block` emits a fixed 8-key schema; NULL fields serialize as `{}`, not omitted

`tools/refresh_r_fixtures.R`'s `dump_block` always writes
coord/cos2/contrib/cor/dist/inertia/v.test/eta2. When the R object lacks a
field (e.g. MFA's `res$ind` has **no** `dist` — `MFA.R:657` lists only
coord/contrib/cos2/within.inertia/coord.partiel), `as.numeric(NULL)` →
`numeric(0)` and jsonlite serializes it as an empty object `{}`, which a test's
`payload.get("dist")` returns as a non-`None` dict → `TypeError` on
`np.asarray(..., float)`. **Don't assert a channel R doesn't actually emit.**
Check the R result's real field list before writing the per-channel test.

### L16 — HMFA/DMFA reuse the MFA/PCA engines; expose internals via the call dict

HMFA is MFA with a per-hierarchy-level `1/λ₁` accumulation, then one weighted
`PCA(XTDC, col.w=poids_top, scale_unit=False)`. The clean first-pass parity
(14/14, no iteration) came from **reusing the already-verified MFA + PCA**: MFA
gained a `weight_col_mfa` arg (threaded into the separate quantitative analyses,
not the data matrix) and exposes `call["XTDC"]` / `["col_w"]` / `["group_mod"]`,
which HMFA's `hweight` re-enters per level (`cw = niv2.col_w * cw`). Lesson for
the MFA family generally: when a method is "built on MFA primitives", expose the
needed internals on the result `call` dict and add narrow optional params rather
than re-implementing — the parity comes for free. **Self-check that generalizes:
the top-level group$coord sums to the eigenvalue per axis** (HMFA, like MFA).
DMFA (A4) is different — it does *per-group standardization* (`scale()` per
level), NOT `1/λ₁` weighting, and its `group$coord` is a trace form
`v_sᵀ Cov_j v_s / λ_s` — so don't assume the MFA weighting pattern there.

### L17 — Doubly sign-ambiguous matrices (rows AND columns) need 2-D alignment

`MFA partial.axes` coord/cor are indexed by each group's *separate*-analysis
axes (rows) and the global axes (columns); both carry arbitrary SVD signs, so a
column-only `align_to_reference` leaves per-row flips (e.g. a group's smallest
separate axis). Fix: align columns, then flip any row whose dot with the
reference is negative (`_align_2d` in `tests/test_mfa.py`). Tell-tale that it's a
benign sign issue and not a bug: the pre-alignment ratio `py/ref` is exactly
±1 across each affected row. Same principle as [[L5]], extended to 2-D.

### L18 — MCA sup blocks route through CA col.sup; Burt is a post-transform

R MCA = `CA(Ztot, col.sup=quali_sup_categories)`, so **quali.sup coord/cos2 are
the CA col.sup projection directly — NO `/√λ` rescale** (the same principal-CA
convention as the active `var$coord`; do not apply the PCA-style barycenter
`/√eig` v.test). quali.sup v.test reuses the active multiplier
`√(n_c(N-1)/(N-n_c))`; quali.sup eta² is the per-variable weighted correlation
ratio of the *individual* coords ([[weighted_eta2]] in `_corr.py`, shared with
FAMD). quanti.sup is the weighted correlation of the sup numeric var with the
individual coords (R uses `svd$U`; scale-invariant). **Burt** is a pure
post-transform of the indicator decomposition: `eig = λ_ind²`, category coord
`= ψ·√λ_ind`, cos² vs the all-axes Burt distance-to-centroid (`auxil`);
`ind`/`contrib`/`eta²` unchanged. Strong checks: `eig_burt == eig_indicator²`
exactly; Burt var coord / indicator var coord `= √λ_ind` per axis.

## Process notes

### P1 — One PR for the whole run, not one per batch

**Context:** the elves skill default is a single PR for the run, with
commits accumulating on the working branch. Reviews happen continuously
on that PR via bots / human / subagent. The user merges at the end. The
plan doc was updated in staging to reflect this convention.

### P2 — Final batch cleans up session artifacts before user merge

**Context:** `docs/elves/survival-guide.md`, `docs/elves/learnings.md`,
`docs/elves/execution-log.md`, and `.elves-session.json` are
operational artifacts that exist during the run for compaction recovery.
The elves skill's Final Completion step (step 7) `git rm`s them before
the PR is ready for human review, so the final PR diff contains only
product code.

The plan doc at `docs/plans/elves-run-1.md` is kept by default
(`cleanup.keep_plan: true` is the elves config default).

---

## Retired Learnings

_(none yet)_
