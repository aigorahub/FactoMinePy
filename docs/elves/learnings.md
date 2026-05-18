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
