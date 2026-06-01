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

- **Planned batches remaining:** 5 (15 of 20 enumerated batches done; + B4b deferred work)
- **Stop allowed right now:** no
- **Why:** 15 done (A1–A4, B1–B5, C1–C3, D1, D2); 5 remain (D3, D4, E1–E3, F1) + B4b.
- **Next required action:** start D3 (textual). Deferred: B4b, Burt+quali_sup, MFA reconst, CaGalt
  type=n/ellipses, meansComp, LinearModel Type-II/stepwise.

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

**Status:** Phase A + B + C done; Phase D in progress. **D1 + D2 complete.** 15 of 20 batches;
everything parity-verified at the deterministic / supplementary bar.

**Active batch:** D2 done → D3 (textual). B4b (missing values + FAMD ind_sup) deferred.

**What was just finished:** D2 — regression family. `LinearModel`/`AovSum` (`linear_model.py`,
contr.sum Type-III ANOVA + per-level Ttest reconstruction) and `RegBest` (`reg_best.py`, best-subset)
— all parity-verified first CI try ([[L24]]); no statsmodels. 231 passed / 2 skipped; rpy2-parity
green (run 26737903399). Commits `9f3e094`, `56a1e39` + close-out. Earlier: Phase A, B1–B5, C1–C3,
D1 (CaGalt).

**Single next action:** tag `elves/pre-batch-d3`, then start D3 (textual) — full spec (from the D3
research subagent) in the Next Exact Batch section below.

---

## Next Exact Batch

**Batch:** D3 — `textual` (free text → document×word contingency table). Low-risk: deterministic
**integer counting**, so parity is exact (atol=0), no SVD/eigen/stochastic. Full D3 research report
in this turn's transcript. `textual` does NOT run a CA — it just builds the table (which then feeds
the already-shipped `descfreq`/`CA`).

**Signature:** `textual(tab, num_text, contingence_by=None, maj_in_min=True, sep_word=None)`.
`num_text` = the free-text column; `contingence_by` = grouping column(s) (default in R is
`1:ncol(tab)`, but the common case is one grouping factor, or `num_text` itself = one row per
document); `maj_in_min` lowercases; `sep_word` = the separator set.

**Tokenizer (replicate R's `chartr`/`strsplit` literally — the whole game):**
- Default `sep.word = "; (),?./:'!=+\n;{}-"` (18 chars incl. space and `\n`). R maps EVERY separator
  char to `";"` via `chartr` (a positional 1:1 map → `str.maketrans({c: ";" for c in SEP})`).
- Then: lowercase **A–Z only** (R's `chartr("A-Z","a-z")`, NOT `str.lower()` — accents differ);
  collapse `";;"→";"` (loop `while ";;" in s`); strip a **leading** `";"` (one-sided — a trailing
  separator leaves a trailing `""` token); `split(";")`.
- Vocabulary = sorted unique tokens (R `as.factor` levels = ASCII/C-locale sort → Python `sorted`).
  Build the groups×words integer count matrix; **no min-frequency filter.**

**Output:** an object/dict with `cont_table` (DataFrame, groups × words, integer counts — a drop-in
`descfreq`/`CA` input) and `nb_words` (DataFrame, columns `words` / `nb.list` = #documents containing
each word, **sorted by descending global frequency**). `contingence_by`: support default (group by
row name = per-document), a single grouping factor (`groupby().sum()`), and the length-2 crossed
factor (`paste(f1,f2,".")`); stacked multi-spec can be deferred. Skip the dead `accent` arg.

**Gaps (additive):** new `factominer/textual.py` + export; new synthetic `datasets/data/textual_synth.csv`
(NO bundled dataset has free text) + `load_textual_synth()` + PROVENANCE (MIT, like `gpa_synth`).

**Fixture (license-clean synthetic, ASCII short sentences + a grouping factor):** ~6 rows, a `review`
text column + a `grp` factor (mixed case to exercise `maj_in_min`; a comma/hyphen to exercise the
separator; NO trailing punctuation, to avoid empty-token JSON-key issues). R call:
`textual(txt, num.text=which(names(txt)=="review"), contingence.by=which(names(txt)=="grp"))`; also a
per-document variant (`contingence.by = num.text`) and optionally `maj.in.min=FALSE`. Dump
`cont.table` + `nb.words`. **Parity = exact integer match (atol=0).**

**Sharp edges:** lowercase A–Z only (not `.lower()`); the trailing-empty-token / one-sided lead-strip;
vocabulary/column order (ASCII sort); keep fixture text ASCII + no trailing punctuation.

**Rollback tag:** `elves/pre-batch-d3` (create before starting).

**Deferred (carry forward):** B4b = missing values (PCA/CA/MCA/GPA) + FAMD `ind_sup`; Burt +
`quali_sup`; MFA `reconst` (all-quanti); CaGalt `type="n"` + `conf_ellip`; `meansComp`; LinearModel
Type-II/AIC-BIC selection; textual stacked multi-spec `contingence_by`.

**After D3:** D4 (utility exports — `svd.triplet`/`tab.disjonctif`/`simule`/`write.infile`, mostly
exposing existing primitives), then E1–E3 (plots for new methods), then F1 (release).

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
