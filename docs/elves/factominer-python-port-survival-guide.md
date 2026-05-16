# ELVES Survival Guide: FactoMineR → Python Port (Full Surface)

READ THIS FILE FIRST before launching, resuming, or compacting this run.

## Run Control

- **Session ID:** `elves-2026-05-16-factominer-python-port-full`
- **Branch:** `claude/plan-factominer-python-port-NkkvY`
- **Base branch:** `main`
- **PR:** none yet; user opens it after morning review
- **Mode:** single overnight, finite. Stops when Batch 18 closeout commits, or earlier if a stop gate fires.
- **Batch sizing:** 19 batches (0–18), ~22 h budget against ~10–12 h of overnight. The `pytest.mark.xfail` policy in the plan's §2 is the pressure valve — niche-method R-parity can hold over without losing the method itself.

## Mission

Ship the full FactoMineR 2.14 surface in Python as `factominer` under `factominer-py/`:

```
Factor methods:        PCA, CA, MCA, FAMD, MFA, HMFA, DMFA, GPA
Clustering:            HCPC
Description:           dimdesc, catdes, condes
Plotting:              matplotlib backend + plotly backend (extras)
Datasets:              decathlon, wine, tea, hobbies, children, geomorphology, milk, gironde, juice, poison, housetasks
Validation:            R + FactoMineR installed in-container; live R fixtures committed; rpy2 lane opt-in
Docs:                  Sphinx site + migrating-from-r cheat sheet + one notebook per method
Release-ready dist:    sdist + wheel built; TestPyPI upload blocked on user token
```

Strictly additive. `factominer-py/` does not import from or get imported by `ml/` or `src/`. The demo runtime path is unchanged.

The full plan, batch breakdown, xfail policy, and explicit risk posture live in `docs/plans/factominer-python-port.md`. That file is the contract; this guide is orientation.

## Read Order On Launch Or Resume

1. `docs/elves/factominer-python-port-survival-guide.md` (this file)
2. `docs/plans/factominer-python-port.md` — especially §2 (xfail policy) and §3 (stop gates)
3. `docs/elves/factominer-python-port-execution-log.md`
4. `.elves-session.json`
5. `AGENTS.md`, `CLAUDE.md`, `README.md`
6. `factominer-py/README.md` (created in Batch 1; the supported-methods table is the live ✓/xfail status board)
7. The most recent test output from the prior batch

## Non-Negotiables

- Clean-room only. Never pull from `/Users/johnennis/aigora/clients/`.
- `.env.local`, pod IDs, volume IDs, tunnel IDs, public IPs, SSH endpoints, HF tokens, TestPyPI tokens stay local-only.
- All new code is MIT. **Do not copy R source from FactoMineR (GPL).** Re-implement from the published PDF + behavior tests.
- Datasets are re-derived from primary public sources; **never lift CSVs out of the R package**. Provenance for each in `factominer/datasets/data/PROVENANCE.md`.
- The port is strictly additive. `factominer-py/` must not be imported by `ml/` or `src/`. The demo runtime path is unchanged.
- `npm run lint`, `npm run typecheck`, `npm run build`, and `python3 -m compileall ml scripts` must continue to pass at every commit.
- Use `NEXT_TELEMETRY_DISABLED=1` on any Node command.
- Do not pause for surveys, feedback prompts, or update prompts.
- **Use the xfail policy honestly.** If R-parity on a niche method (HMFA, DMFA, GPA, MCA edge case) refuses to converge within 30 min of retry, mark the test `pytest.mark.xfail(strict=True, reason="R-parity not yet reached")`, document the known limitation in the method's docstring + Sphinx page, and move on. Do **not** silently widen tolerances to fake green.

## Preflight

```bash
PROFILE_NOTES_ALLOW_SLEEPING_RUNTIME=1 NEXT_TELEMETRY_DISABLED=1 bash scripts/elves-preflight.sh
```

A known unrelated failure exists at `scripts/check_open_ends_ui_copy.py`. It is the **only** preflight failure to tolerate. Any other failure trips the stop gate.

## Container Bootstrap (Batch 0)

Ubuntu 24.04 with `apt`. R installs cleanly:

```bash
sudo apt-get update -y
sudo apt-get install -y r-base r-base-dev libxml2-dev libcurl4-openssl-dev libssl-dev
sudo Rscript -e 'install.packages(c("FactoMineR","jsonlite"), repos="https://cloud.r-project.org")'

python3 -m venv .venv-factominer
.venv-factominer/bin/pip install -U pip wheel
.venv-factominer/bin/pip install -r factominer-py/requirements-dev.txt    # created in Batch 1
```

If `apt` install of R fails, fall back to `conda` if available; if both fail, degrade per plan §3 stop-gate #3 (skip parity, ship with structural-invariant + scientisttools-snapshot tests only, surface to user). Do **not** label methods as parity-verified when R never ran.

## Stop Gates (abort and report, no silent recovery)

1. Preflight fails for any reason other than the known open-ends UI copy guard.
2. Foundation invalid: `scientisttools` doesn't install, or its PCA on decathlon is structurally broken (NaNs, wrong shape, eigenvalues miss the trace by > 1e-6).
3. R install fails *and* both fallbacks (conda, alternate apt repo) fail. Degrade and surface.
4. Repo's existing checks regress (`npm run lint`/`typecheck`/`build`, `python3 -m compileall ml scripts`).
5. Working tree drifts outside `factominer-py/` + the plan + survival-guide + execution-log + learnings + `.elves-session.json` without a written justification in the execution log.
6. Three consecutive red batches (tests *and* fix attempts red).

When a gate fires: write final status into the execution log, commit, push, stop. Leave partial work on the branch; do not roll back.

## Batch Cheat Sheet

Full detail in `docs/plans/factominer-python-port.md` §5. Quick reference:

| # | Name | Exit |
| --- | --- | --- |
| 0 | Preflight + container prep | R + FactoMineR + scientisttools all callable |
| 1 | Skeleton + Result contract + sign convention | `pip install -e` works, sign convention idempotent |
| 2 | Datasets + R-fixture harness | 11 datasets bundled, R fixtures committed |
| 3 | PCA | R-parity green on decathlon + wine |
| 4 | CA | R-parity green on children |
| 5 | MCA | R-parity green on tea + hobbies |
| 6 | FAMD | R-parity green on geomorphology |
| 7 | MFA | R-parity green on wine multi-group |
| 8 | HMFA (from primitives) | structural invariants + R-parity or honest xfail |
| 9 | DMFA (from primitives) | structural invariants + R-parity or honest xfail |
| 10 | GPA (from primitives) | structural invariants + R-parity or honest xfail |
| 11 | HCPC | ARI ≥ 0.999 vs R on PCA(wine), MCA(tea) |
| 12 | dimdesc / catdes / condes | p-values / v-test match R to 1e-6 |
| 13 | matplotlib backend Part 1 (factor maps, scree, biplot) | snapshot tests green |
| 14 | matplotlib backend Part 2 (HCPC, ellipses) | snapshot tests green |
| 15 | plotly backend | figure-JSON structural tests green |
| 16 | Examples + Sphinx docs | one executed notebook per method, sphinx-build clean |
| 17 | rpy2 parity lane + CI | `pytest -m rpy2` lane wired into CI |
| 18 | Release-ready dist + closeout | `python -m build` clean, `twine check` clean, learnings written |

Each batch ends with: commit, push to `claude/plan-factominer-python-port-NkkvY`, append a dated entry to `docs/elves/factominer-python-port-execution-log.md`.

## Subagent Use

Allowed and encouraged where it doesn't break coherence (plan §7). Subagents may **investigate, draft, read R output, generate scratch notes**. Subagents may **not** push to git. Pushes happen only from the main agent at batch boundaries.

Concrete subagent uses:
- Batch 2: parallel dataset re-derivation (one subagent per dataset).
- Batches 3–7: subagent drives R from CLI to dump alternative-option outputs while main agent codes.
- Batches 8–10: subagent extracts math from the FactoMineR PDF into `notes/<method>.md` (scratch, not committed) while main agent implements.
- Batch 13: subagent generates baseline snapshot images per plot type.
- Batch 16: subagent drafts one notebook per method while main agent finalizes Sphinx structure.

## Definition of Done

The user can:

1. `git fetch && git checkout claude/plan-factominer-python-port-NkkvY`
2. `cd factominer-py && pip install -e .[dev,plotly]`
3. `pytest -q` — all green or only documented `xfail` red; `xfail`s match the supported-methods table in the README and the §2 policy in the plan
4. `python -c "from factominer import PCA, CA, MCA, FAMD, MFA, HMFA, DMFA, GPA, HCPC, dimdesc, catdes, condes; from factominer.datasets import load_decathlon; res = PCA(load_decathlon()); print(res.summary())"` — sane output for every name
5. Open the executed notebook for any method under `factominer-py/docs/examples/` and see real eigenvalues, plots, partitions
6. `sphinx-build -b html factominer-py/docs factominer-py/docs/_build/html` clean
7. `factominer-py/dist/factominer-0.1.0-py3-none-any.whl` and `factominer-py/dist/factominer-0.1.0.tar.gz` present and pass `twine check`
8. Read the README "Status" section and know exactly which methods are R-parity-verified, which are xfail'd with a parity gap, and the exact remaining work for each xfail (typically: one tolerance to chase, one option to align with R)

If any of those eight are not true at branch HEAD, the run is not done.

## Time Budget

~22 h plan vs ~10–12 h available overnight. The plan calibrates to push hard; the xfail policy is the honest pressure valve. Expected morning state:

- **Highly likely live + R-parity verified:** PCA, CA, MCA, FAMD, MFA, HCPC, dimdesc/catdes/condes.
- **Live with possible xfail on niche parity:** HMFA, DMFA, GPA.
- **Live, no parity to chase:** plotly backend, Sphinx site.
- **Always skipped (token-gated):** TestPyPI upload.

If Batch 2 (datasets + R fixtures) overruns by 60+ min, the cheapest cut is Batch 15 (plotly backend) — fall back to matplotlib-only and note plotly as deferred in the README. Do not cut Batches 0, 1, 2, 3, 11, 12, 13, 14, 16, 18.
