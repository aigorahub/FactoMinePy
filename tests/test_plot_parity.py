"""Plot-data parity tests against R FactoMineR.

R's ``plot.PCA/.CA/.MCA/.HCPC`` draw to a device and return no extractable
data, and the raw coordinates they plot are already parity-tested by
test_pca/test_ca/test_mca. The one genuinely-derived display quantity the
analysis layer does not already expose is the confidence/concentration
ellipse, computed by R's ``coord.ellipse`` with a specific parametrization
(``t·scale·cos(a ± d/2)``, ``d = acos(r)``). ``factominer.plot._data.coord_ellipse``
ports that exactly; these tests assert vertex-level parity.

The primary test is a pure-formula check: feed R's own input coordinates back
through ``coord_ellipse`` and compare to R's ellipse output (no sign ambiguity).
A second test runs the full PCA → ellipse pipeline, sign-aligning our
coordinates to R's first.
"""

from __future__ import annotations

import numpy as np

from factominer import PCA
from factominer._sign import align_to_reference
from factominer.datasets import load_decathlon
from factominer.plot._data import coord_ellipse


def _coords_and_groups(fixture):
    cs = fixture["coord_simul"]
    groups = [row["Competition"] for row in cs]
    coords = np.array([[row["Dim.1"], row["Dim.2"]] for row in cs], dtype=np.float64)
    return coords, groups


def _r_ellipse_by_group(payload):
    out: dict[str, np.ndarray] = {}
    for row in payload:
        lev = str(row["Competition"])
        out.setdefault(lev, []).append([row["Dim.1"], row["Dim.2"]])
    return {k: np.asarray(v, dtype=np.float64) for k, v in out.items()}


def test_coord_ellipse_indiv_formula(r_plot_ellipse_decathlon):
    """Pure formula parity: R's input coords → our ellipse == R's ellipse."""
    coords, groups = _coords_and_groups(r_plot_ellipse_decathlon)
    py = coord_ellipse(coords, groups, axes=(0, 1), level=0.95, npoint=100, bary=False)
    r = _r_ellipse_by_group(r_plot_ellipse_decathlon["ellipse_indiv"])
    assert set(py) == set(r)
    for lev, r_pts in r.items():
        assert py[lev].shape == r_pts.shape == (100, 2)
        assert np.allclose(py[lev], r_pts, atol=1e-9, rtol=0), f"group {lev}"


def test_coord_ellipse_bary_formula(r_plot_ellipse_decathlon):
    """Concentration ellipse (bary=True) parity on R's own coords."""
    coords, groups = _coords_and_groups(r_plot_ellipse_decathlon)
    py = coord_ellipse(coords, groups, axes=(0, 1), level=0.95, npoint=100, bary=True)
    r = _r_ellipse_by_group(r_plot_ellipse_decathlon["ellipse_bary"])
    for lev, r_pts in r.items():
        assert np.allclose(py[lev], r_pts, atol=1e-9, rtol=0), f"group {lev}"


def test_coord_ellipse_end_to_end(r_plot_ellipse_decathlon):
    """Full pipeline: our PCA individuals (sign-aligned to R) → ellipse == R."""
    df = load_decathlon()
    res = PCA(df, scale_unit=True, ncp=5, quanti_sup=["Rank", "Points"], quali_sup=["Competition"])
    r_coords, groups = _coords_and_groups(r_plot_ellipse_decathlon)
    our = res.ind.coord.to_numpy()[:, :2]
    our_aligned = align_to_reference(our, r_coords)
    py = coord_ellipse(our_aligned, df["Competition"], axes=(0, 1), level=0.95, npoint=100)
    r = _r_ellipse_by_group(r_plot_ellipse_decathlon["ellipse_indiv"])
    for lev, r_pts in r.items():
        assert np.allclose(py[lev], r_pts, atol=1e-8, rtol=0), f"group {lev}"
