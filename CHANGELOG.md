# Changelog

All notable changes to FactoMinePy are tracked here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) once
out of pre-release.

## [Unreleased]

### Added

- **`GPA` unequal-width configurations + `correlations` / `PANOVA`.** GPA now
  handles configurations of different column counts (the equal-width restriction
  is lifted): each calibrated configuration is padded to `max(group)` and the
  Procrustes congruence uses a symmetric, width-agnostic form. Adds the
  per-configuration `correlations` (original variables vs the consensus axes) and
  the `PANOVA` (Procrustes ANOVA) sum-of-squares tables. `RV`/`RVs`/`simi` and the
  PANOVA per-object/per-config tables are parity-verified exactly against live R
  FactoMineR 2.14; `consensus`/`Xfin`/`correlations` match up to the global
  rotation/reflection gauge (R's GPA is stochastic). Missing values remain
  unsupported.
- **`MCA` supplementary blocks + Burt method.** MCA now computes the
  supplementary-variable blocks (`quanti_sup` correlations with the axes;
  `quali_sup` category barycenters with cos²/v.test and per-variable eta²) — the
  arguments were previously accepted but the blocks were never produced. The
  `method="Burt"` option is now a true Burt analysis (eigenvalues squared,
  coordinates rescaled by √λ, cos² against the all-axes Burt distance) rather
  than silently returning the indicator result. Both are parity-verified against
  live R FactoMineR 2.14 on the tea dataset. Burt is not yet combined with
  `quali_sup`.
- **`FAMD` supplementary variables** (`sup_var`): FAMD now projects
  supplementary quantitative variables (correlations with the axes) and
  supplementary qualitative variables (category barycenters with cos²/v.test/
  eta²), routed through the inner PCA's sup machinery, plus the combined
  `var.coord_sup` / `var.cos2_sup` summary. Parity-verified against live R
  FactoMineR 2.14 on `FAMD(poison, sup.var=c("Time","Sex"))`. Supplementary
  individuals (`ind_sup`) are not yet supported.
- **`DMFA` (Dual Multiple Factor Analysis)** is now implemented
  (`factominer/dmfa.py` + a `DMFAResult` container), completing the MFA family
  (MFA, HMFA, DMFA all live). DMFA studies how the cloud of variables varies
  across the levels of a grouping factor: each group's sub-table is standardized
  by its own mean/sd, the per-group-centered sub-tables are stacked, a plain PCA
  (the factor as supplementary qualitative) is run, and each group is placed by
  the trace `group.coord[j,s] = v_sᵀ Cov_j v_s / λ_s`. Outputs `eig`, `ind`
  (reordered to input order), `var`, `quanti.sup`, the group block
  (`coord`/`coord.n`/`cos2`), and the per-group `cor.dim.gr` / `var.partiel`
  diagnostics. Parity-verified against live R FactoMineR 2.14 on
  `DMFA(decathlon, num.fact="Competition", quanti.sup=Rank/Points)`.
  Supplementary qualitatives are not yet supported.
- **`HMFA` (Hierarchical Multiple Factor Analysis)** is now implemented
  (`factominer/hmfa.py` + an `HMFAResult` container). HMFA generalizes MFA to a
  hierarchy of groups (`H`, a list of per-level group counts): each hierarchy
  level multiplies in another `1/λ₁` normalization, then a single weighted PCA
  on the level-1-standardized matrix yields the analysis. Outputs `eig`, `ind`,
  `quanti.var`, `quali.var`, `group.coord` (one matrix per hierarchy level),
  `group.canonical` (canonical correlations), and the per-level partial
  coordinate arrays. Parity-verified column-by-column against live R FactoMineR
  2.14 on a categorical 2-level poison hierarchy and a pure-quantitative
  decathlon hierarchy. Group types `"s"`/`"c"`/`"n"`, active groups, uniform
  row weights. As part of this, `MFA` gained a `weight_col_mfa` argument and
  exposes its internal data matrix / column weights / expanded group sizes,
  which HMFA reuses per level.

- **`MFA` (Multiple Factor Analysis)** is now implemented
  (`factominer/mfa.py` + an `MFAGroup` result container). MFA runs a single
  global weighted PCA on the per-group-normalized (`1/λ₁`) concatenation of the
  groups; the eigen-step is delegated to `factominer.PCA`
  (`scale_unit=False`, `col_w=ponderation`), mirroring how R delegates to
  `FactoMineR::PCA`. Supports group types `"s"` (standardized-quantitative),
  `"c"` (centered-quantitative), and `"n"` (categorical). Outputs `eig`, `ind`,
  `quanti.var`, `quali.var`, and the `group` block (coordinates, contributions,
  cos², dist², and the `Lg` / `RV` matrices including the global "MFA" row).
  Parity-verified column-by-column against live R FactoMineR 2.14 on the
  canonical `MFA(poison, group=c(2,2,5,6), type=c("s","n","n","n"))` example.
  Also exposes the partial-factor-map machinery: `ind.coord_partiel` (per-group
  partial individual coordinates), `group.correlation`, `partial_axes`
  (coordinates/correlations/contributions of each group's separate principal
  axes with the global axes), and `inertia_ratio` — all parity-verified.
  Active groups with uniform row weights; supplementary groups and
  frequency/mixed (`"f"`/`"m"`) groups are not yet supported.

## [0.2.0.dev0] — 2026-05-30

This release adds two FactoMineR methods (FAMD, GPA) and a plotly plotting
backend, tightens every parity tolerance, and verifies all fixtures
byte-for-byte against live R FactoMineR 2.14.

### Added

- **`GPA` (Generalized Procrustes Analysis)** is now implemented
  (`factominer/gpa.py` + a `GPAResult` dataclass). R's GPA is stochastic
  (random multi-start + `rnorm` rank-deficient basis completion), so the
  port implements the deterministic single-start core and validates in two
  tiers: `RV` / `RVs` / `simi` (from the raw configurations, including the
  Kazi-Aoual standardized `RVstd`) match R **exactly**; `consensus` / `Xfin`
  match R **up to a global rotation/reflection** (verified via inter-object
  distance matrices). Currently limited to no-missing, equal-width
  configurations. Ships a fully-reproducible synthetic GPA dataset
  (`load_gpa_synth`).
- **Plotly plotting backend** (`factominer/plot/plotly_backend.py`),
  selected via `plot(res, ..., backend="plotly")`, returning
  `plotly.graph_objects.Figure`. Mirrors the full matplotlib surface
  (PCA ind/var/biplot, scree, contrib; CA/MCA row/col/biplot maps; HCPC
  factor map + dendrogram) and draws from the same `_data` geometry layer
  (shared palette + R-faithful ellipses). Added `plotly` to the `dev`
  extra; it remains an optional runtime dependency
  (`pip install 'factominer[plotly]'`).
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

[Unreleased]: https://github.com/aigorahub/FactoMinePy/compare/v0.2.0.dev0...HEAD
[0.2.0.dev0]: https://github.com/aigorahub/FactoMinePy/compare/v0.1.0.dev0...v0.2.0.dev0
[0.1.0.dev0]: https://github.com/aigorahub/FactoMinePy/releases/tag/v0.1.0.dev0
