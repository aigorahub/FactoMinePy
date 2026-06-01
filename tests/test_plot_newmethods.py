"""Structural smoke tests for plotting the newer methods.

The factor-map coordinates are already parity-verified per method; here we only
check that the plot layer *accepts* FAMD / MFA / HMFA / DMFA / CaGalt and draws
the ``ind`` / ``var`` / ``scree`` charts without error on both backends. There is
no R numeric fixture for plots — parity here is structural.
"""

from __future__ import annotations

import matplotlib
import pytest

matplotlib.use("Agg")

from factominer import DMFA, FAMD, HMFA, MFA, CaGalt  # noqa: E402
from factominer.datasets import (  # noqa: E402
    load_cagalt_synth,
    load_decathlon,
    load_poison,
)
from factominer.plot import plot  # noqa: E402


def _models():
    poison = load_poison()
    cg = load_cagalt_synth()
    return {
        "FAMD": FAMD(poison),
        "MFA": MFA(poison, group=[2, 2, 5, 6], type=["s", "n", "n", "n"],
                   name_group=["desc", "desc2", "symptom", "eat"]),
        "HMFA": HMFA(poison, H=[[2, 2, 5, 6], [2, 2]], type=["s", "n", "n", "n"]),
        "DMFA": DMFA(load_decathlon(), num_fact="Competition", quanti_sup=["Rank", "Points"]),
        "CaGalt": CaGalt(cg.iloc[:, :6], cg.iloc[:, 6:9]),
    }


MODELS = _models()


@pytest.mark.parametrize("name", list(MODELS))
@pytest.mark.parametrize("choix", ["ind", "var", "scree"])
@pytest.mark.parametrize("backend", ["matplotlib", "plotly"])
def test_plot_new_method(name, choix, backend):
    out = plot(MODELS[name], choix=choix, backend=backend)
    assert out is not None


def test_plot_ind_point_count():
    # The individuals scatter should carry one point per individual.
    res = MODELS["MFA"]
    ax = plot(res, choix="ind", backend="matplotlib")
    n_pts = sum(c.get_offsets().shape[0] for c in ax.collections)
    assert n_pts >= res.ind.coord.shape[0]
