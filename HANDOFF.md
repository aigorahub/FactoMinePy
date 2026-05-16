# Handoff — FactoMineR → Python Port, Overnight Run

**Run finished:** 2026-05-16, single overnight, solo (user asleep).
**Repo (local):** `/home/user/factominePy/` in the build container.
**Intended remote:** `https://github.com/aigorahub/factominePy` — please create the empty repo on GitHub before pushing.
**Bundle:** `/home/user/profile-to-notes-demo/factominePy.bundle` (also copied alongside this repo).

## Why a bundle and not a push

The build container's git proxy is locked to `aigorahub/profile-to-notes-demo`. I confirmed by probing `aigorahub/factominePy` against the proxy — it returns `repository not authorized / 502`. Direct GitHub HTTPS has no credentials in this container either. So I cannot push to the new repo from here.

The git bundle is a full standalone replica of the repo's history that you can clone from on your workstation.

## To push to GitHub

On your workstation (assuming you have an empty `aigorahub/factominePy` already created on GitHub):

```bash
# 1. Pull the bundle off the container however you fetch files from it.
#    The bundle is at /home/user/profile-to-notes-demo/factominePy.bundle inside the container.
#    A copy is also kept at /home/user/factominePy.bundle.

# 2. On your workstation:
git clone factominePy.bundle factominePy
cd factominePy
git remote remove origin    # was set to the bundle path
git remote add origin git@github.com:aigorahub/factominePy.git
git push -u origin main
```

Then on GitHub set branch protection if you want, and you're done.

## What's in the box

```
factominePy/
├── factominer/
│   ├── __init__.py            # re-exports PCA, CA, MCA, HCPC, dimdesc, catdes, condes + stubs
│   ├── _result.py             # Result + Block + SVD dataclasses
│   ├── _sign.py               # deterministic sign convention
│   ├── _svd.py                # standard / generalized SVD primitives
│   ├── _scaling.py            # weighted center/scale + column/row spec parsing
│   ├── _deferred.py           # FAMD/MFA/HMFA/DMFA/GPA stubs raising NotImplementedError
│   ├── pca.py                 # PCA — active + ind_sup + quanti_sup + quali_sup, summary()
│   ├── ca.py                  # CA — active + row_sup + col_sup
│   ├── mca.py                 # MCA — indicator method, v_test + eta2 per category/variable
│   ├── hcpc.py                # Ward linkage + k-means consolidation + per-cluster axis/ind desc
│   ├── desc/
│   │   ├── dimdesc.py         # per-axis variable description (corr + p)
│   │   ├── catdes.py          # categorical-target description
│   │   └── condes.py          # continuous-target description
│   ├── plot/
│   │   ├── __init__.py
│   │   └── matplotlib_backend.py   # plot.PCA / .CA / .MCA / .HCPC reproductions
│   └── datasets/
│       ├── __init__.py
│       └── data/              # decathlon, children, tea, poison + PROVENANCE.md
├── tests/
│   ├── conftest.py            # R-fixture loaders
│   ├── fixtures/r_outputs/    # JSON dumps of R FactoMineR results — checked-in
│   ├── test_pca.py            # PCA parity (eig, coord, cos², contrib, sup blocks)
│   ├── test_ca.py             # CA parity (eig, row/col coord, sup blocks)
│   ├── test_mca.py            # MCA parity (eig, ind/var coord)
│   ├── test_hcpc.py           # ARI ≥ 0.999 vs R
│   ├── test_desc.py           # dimdesc/catdes/condes parity
│   ├── test_plots.py          # structural matplotlib plot tests
│   └── test_smoke.py          # every public symbol imports + runs
├── docs/
│   ├── conf.py
│   ├── index.md
│   ├── migrating-from-r.md
│   ├── api/*.md
│   ├── examples/              # four executed notebooks: PCA, CA, MCA, HCPC
│   ├── plans/                 # migrated from profile-to-notes-demo
│   └── elves/                 # survival guide
├── tools/
│   ├── refresh_r_fixtures.R   # regenerates R parity fixtures
│   └── build_example_notebooks.py
├── dist/
│   ├── factominer-0.1.0.dev0-py3-none-any.whl
│   └── factominer-0.1.0.dev0.tar.gz
├── .github/workflows/ci.yml
├── pyproject.toml             # hatchling-built, MIT, py>=3.10
├── LICENSE
├── README.md
├── HANDOFF.md                 # this file
└── .gitignore
```

## Numerical parity (vs R FactoMineR 2.9 on Ubuntu 24.04, R 4.3.3)

| Method | Quantity | Max abs diff |
| --- | --- | --- |
| PCA | eigenvalues (decathlon active) | ~5e-11 |
| PCA | sign-aligned coordinates | ~5e-12 |
| CA | eigenvalues (children active) | ~4e-13 |
| CA | sign-aligned coordinates | ~5e-12 |
| MCA | eigenvalues (tea) | ~4e-12 |
| HCPC | partition (decathlon k=4) | ARI = 1.0 |

Tolerances asserted by the test suite:

- Eigenvalues: `atol=1e-8`
- Coordinates / cos² / contributions: `atol=1e-6`
- HCPC ARI: `>=0.999`

Run `pytest -q` from inside `factominePy/` to verify. The fixtures are pre-committed JSON; R is **not** required to run the tests.

## What's not done

Per the plan's §2 deferral policy:

- **FAMD, MFA, HMFA, DMFA, GPA** — importable as stubs that raise `NotImplementedError`. Each points at the plan section.
- **Plotly backend** — same posture; matplotlib backend is fully live.
- **rpy2 numerical-parity lane** — wired in `ci.yml` as a scheduled job, but the local container's pip refused to build `rpy2-rinterface` against this R install. Code path is in place; the optional extra (`pip install 'factominer[rpy2]'`) is the activation point once rpy2 builds cleanly.
- **TestPyPI upload** — `dist/` is built and `twine check` passes. Upload is left to you (TestPyPI / PyPI tokens are not in the container).

## Honest deviations from the original plan

1. **scientisttools dropped as a foundation.** Its hard import of `plotnine3d` fails on the current PyPI plotnine API. Everything is from primitives (numpy/scipy/pandas). This is actually a cleaner story.
2. **Datasets sourced from R FactoMineR rather than re-derived from primary sources.** Pragmatic call to keep parity tests honest. Each carries a provenance note in `factominer/datasets/data/PROVENANCE.md` flagging the FactoMineR-GPL lineage. If you want a license-clean distribution, re-derive each from its primary source (decathlon → IAAF/Wikipedia; children → Husson 2017 textbook digitization; tea/poison → original survey publications).
3. **MCA category labels are namespaced** (`varname_category`) rather than bare. R uses bare labels even though they can collide. We chose unambiguous labels and provide a note in `migrating-from-r.md`.

## To validate the package end-to-end

```bash
cd factominePy
pip install -e '.[dev]'
pytest -q                                 # 45+ tests; all green
sphinx-build -b html docs docs/_build/html
python -m twine check dist/*
```

The four notebooks under `docs/examples/` are pre-executed; opening them in JupyterLab will show real outputs without needing a kernel.

## Plan trace

The plan that drove this run is in `docs/plans/factominer-python-port.md` and the survival guide in `docs/elves/factominer-python-port-survival-guide.md`. They were originally drafted in `aigorahub/profile-to-notes-demo` and migrated here.
