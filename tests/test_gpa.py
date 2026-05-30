"""GPA parity tests against R FactoMineR — two-tier.

R's GPA is stochastic (random multi-start + rnorm basis completion), so an
exact match on the aligned coordinates (``consensus`` / ``Xfin``) is not
achievable — those are only defined up to a global rotation/reflection anyway
(the gauge freedom of Procrustes analysis). The port implements the
deterministic single-start core and is validated in two tiers:

- **Tier 1 (exact, atol 1e-6):** ``RV``, ``RVs``, ``simi`` are computed from the
  *raw* configurations and are rotation/scale-invariant, so they match R
  exactly regardless of the random restart.
- **Tier 2 (rotation-invariant):** ``consensus`` and ``Xfin`` are compared via
  their pairwise inter-object Euclidean distance matrices, which are invariant
  to the residual rotation/reflection gauge.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial.distance import pdist

from factominer import GPA
from factominer.datasets import load_gpa_synth

GROUP = [2, 2, 2]
NAMES = ["group.1", "group.2", "group.3"]


def _gpa():
    return GPA(load_gpa_synth(), group=GROUP, scale=True)


def _kxk(rows, names):
    """Parse R's as.data.frame(K×K matrix) row-list into an ordered array."""
    by_row = {str(r.get("_row") or r.get("rowname")): r for r in rows}
    return np.array([[by_row[ri][ci] for ci in names] for ri in names], dtype=np.float64)


def _coords(rows):
    """Pull the numeric coordinate columns (drop the _row label) in order."""
    keys = [k for k in rows[0] if k not in ("_row", "rowname")]
    return np.array([[r[k] for k in keys] for r in rows], dtype=np.float64)


# ---------------------------------------------------------------------------
# Tier 1 — exact, deterministic (computed from raw configs)
# ---------------------------------------------------------------------------


def test_gpa_rv(r_gpa_synth):
    res = _gpa()
    r = _kxk(r_gpa_synth["RV"], NAMES)
    assert np.allclose(res.RV.loc[NAMES, NAMES].to_numpy(), r, atol=1e-6, rtol=0)


def test_gpa_rvs(r_gpa_synth):
    res = _gpa()
    r = _kxk(r_gpa_synth["RVs"], NAMES)
    assert np.allclose(res.RVs.loc[NAMES, NAMES].to_numpy(), r, atol=1e-6, rtol=0)


def test_gpa_simi(r_gpa_synth):
    res = _gpa()
    r = _kxk(r_gpa_synth["simi"], NAMES)
    assert np.allclose(res.simi.loc[NAMES, NAMES].to_numpy(), r, atol=1e-6, rtol=0)


# ---------------------------------------------------------------------------
# Tier 2 — rotation-invariant (consensus / Xfin via distance matrices)
# ---------------------------------------------------------------------------


def test_gpa_consensus_distances(r_gpa_synth):
    res = _gpa()
    r_consensus = _coords(r_gpa_synth["consensus"])
    py = res.consensus.to_numpy()
    assert py.shape == r_consensus.shape, f"{py.shape} vs {r_consensus.shape}"
    # Inter-object distance matrix is invariant to rotation/reflection.
    assert np.allclose(pdist(py), pdist(r_consensus), atol=1e-6, rtol=0)


def test_gpa_xfin_distances(r_gpa_synth):
    res = _gpa()
    xfin = r_gpa_synth["Xfin"]
    for k in range(len(GROUP)):
        r_xf = _coords(xfin[k])
        py = res.Xfin[k].to_numpy()
        assert np.allclose(pdist(py), pdist(r_xf), atol=1e-6, rtol=0), f"config {k}"


def test_gpa_scaling_present(r_gpa_synth):
    """Scaling weights (poids) are gauge-invariant; they should match R when
    both reach the same optimum. Asserted loosely (the stochastic multi-start
    can in principle reach a different equivalent optimum)."""
    res = _gpa()
    r_scaling = np.asarray(r_gpa_synth["scaling"], dtype=np.float64)
    py = res.scaling.to_numpy()
    assert py.shape == r_scaling.shape
    # Scaling weights are positive and normalized; compare up to a small tol.
    assert np.allclose(py, r_scaling, atol=1e-4, rtol=0), f"py={py}, r={r_scaling}"


def test_gpa_structure():
    res = _gpa()
    assert res.RV.shape == (3, 3)
    assert np.allclose(np.diag(res.RV.to_numpy()), 1.0)
    assert (res.scaling > 0).all()
    assert len(res.Xfin) == 3
