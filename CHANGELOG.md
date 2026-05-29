# Changelog

All notable changes to FactoMinePy are tracked here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) once
out of pre-release.

## [Unreleased]

### Added

- **Backend-agnostic plot-data layer** (`factominer/plot/_data.py`) with a
  faithful port of R FactoMineR's `coord.ellipse`
  (`t·scale·cos(a ± d/2)`, `d = acos(r)`, `t = sqrt(qchisq(level, 2))`).
  The matplotlib backend now draws confidence/concentration ellipses from
  this shared source, so they are **vertex-identical to R** (previously the
  backend used an eigenvector + matplotlib `Ellipse` form that was only
  geometrically equivalent). Verified by `tests/test_plot_parity.py` for
  both `bary=False` and `bary=True` at 1e-9.
- **`FAMD` (Factor Analysis of Mixed Data)** is now implemented and parity-
  verified against R FactoMineR 2.14 on the `poison` dataset (active
  variables). Mirrors R's approach of running an unscaled PCA on the mixed
  `[standardized-quanti | centered/sqrt(prop)-scaled indicator]` matrix.
  Exposes `eig` (truncated to `ncp`), `ind`, `quanti_var`, `quali_var`
  (with the principal category coordinate, cos², contrib, v.test), and the
  combined `var` summary (squared loadings for quanti, eta² for quali).
  `Result` gains `quanti_var` / `quali_var` Block fields. Supplementary
  variables/individuals are not yet supported.
- Full FactoMineR 2.14 schema parity for `dimdesc` / `catdes` / `condes`
  (`n` column on quanti tables; `Cla/Mod` / `Mod/Cla` / `Global` /
  hypergeometric `v.test` on catdes category; `Eta2` / `P-value` on
  catdes quanti.var; `sd in category` / `Overall sd` / `n` on catdes
  per-level quanti; `Estimate` / `p.value` on condes category).
- PCA now exposes `quali.sup$eta2` (per-variable, not per-category).
- PCA / CA / MCA `res$eig` now carries all eigenvalues (only the
  coord / cos² / contrib blocks are truncated to `ncp`); `res$svd$vs`
  keeps the full singular spectrum.
- MCA `res$eig` truncated to `total_cat - q_vars` to match R's
  "useful" axis count.
- HCPC `data_clust` holds the original input X + `clust` column (was:
  PC coordinates); `desc_var` populated via the parity-verified
  `catdes`; `desc_axes` via `condes` per axis.
- CI: `rpy2-parity` workflow installs FactoMineR 2.14 from CRAN, runs
  the parity suite against freshly generated fixtures, and uploads the
  fresh fixtures + drift diff as artifacts. Triggerable on-demand via
  `workflow_dispatch`; runs weekly on Monday cron.
- README: experimental-use-with-caution callout, known limitations
  section, tightened parity-tolerance documentation.
- Open-source meta files (this CHANGELOG, CONTRIBUTING.md, CITATION.cff,
  SECURITY.md, issue + PR templates).

### Fixed

- MCA `var$eta2` and `var$v.test`: dropped erroneous `/lambda_k` and
  `/sqrt(lambda_k)` factors. R FactoMineR's MCA `var$coord` is the
  standard category coordinate ψ_c, so:
  - `eta²(v,k) = sum_c n_c * ψ_c² / N`
  - `v.test(c,k) = ψ_c * sqrt(n_c (N-1) / (N - n_c))`
  Output now matches R to 1e-9 on the tea fixture (previously off by
  ~6.7× on eta² and ~2.6× on v.test).
- Sphinx build: enabled `myst-nb` so example notebooks under
  `docs/examples/` actually render. (Listing both `myst_parser` and
  `myst_nb` in `extensions` double-invokes `setup_sphinx` and crashes
  myst-parser 5.1.0; only `myst_nb` is loaded now.)
- `docs/api/datasets.md`: relative PROVENANCE.md link rewritten to an
  absolute GitHub URL so it resolves outside the repo tree.

### Changed

- `tools/refresh_r_fixtures.R` adds two richer fixtures
  (`condes/tea_age.json`, `dimdesc/pca_decathlon_proba50.json`) that
  exercise the populated-quali + populated-category branches of the
  desc functions.
- Test tolerances tightened across the suite:
  - eigenvalues: `1e-8 → 1e-10`
  - coord / cos² / cor / eta²: `1e-6 → 1e-9`
  - contrib: `1e-6 → 1e-8`
  - v.test: still 1e-6 (limited by chained qnorm / hypergeometric)
  - p-values: `1e-5` relative (new — previously untested at column level)

## [0.1.0.dev0] — 2026-05-16

Initial port: PCA, CA, MCA, HCPC, dimdesc / catdes / condes with R-parity
tests. FAMD / MFA / HMFA / DMFA / GPA importable as `NotImplementedError`
stubs.

[Unreleased]: https://github.com/aigorahub/FactoMinePy/compare/v0.1.0.dev0...HEAD
[0.1.0.dev0]: https://github.com/aigorahub/FactoMinePy/releases/tag/v0.1.0.dev0
