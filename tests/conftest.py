"""Pytest fixtures shared across the test suite."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

R_FIXTURES = Path(__file__).parent / "fixtures" / "r_outputs"


def _load_r_fixture(method: str, dataset: str) -> dict:
    path = R_FIXTURES / method / f"{dataset}.json"
    if not path.exists():
        pytest.skip(f"missing R fixture: {path}")
    return json.loads(path.read_text())


def _as_df(payload: list | None, label: str) -> pd.DataFrame | None:
    if not payload:
        return None
    rows = pd.DataFrame(payload)
    # jsonlite serializes data.frames as list-of-objects with a row-name key (e.g. "_row")
    # depending on options. Detect and strip.
    for cand in ("_row", "rowname", "X"):
        if cand in rows.columns:
            rows = rows.set_index(cand)
            rows.index.name = label
            break
    # numeric coercion where possible
    for c in rows.columns:
        rows[c] = pd.to_numeric(rows[c], errors="ignore")
    return rows


@pytest.fixture(scope="session")
def r_pca_decathlon() -> dict:
    return _load_r_fixture("pca", "decathlon")


@pytest.fixture(scope="session")
def r_pca_decathlon_plain() -> dict:
    return _load_r_fixture("pca", "decathlon_plain")


@pytest.fixture(scope="session")
def r_pca_decathlon_roww() -> dict:
    return _load_r_fixture("pca", "decathlon_roww")


@pytest.fixture(scope="session")
def r_ca_children() -> dict:
    return _load_r_fixture("ca", "children")


@pytest.fixture(scope="session")
def r_ca_children_plain() -> dict:
    return _load_r_fixture("ca", "children_plain")


@pytest.fixture(scope="session")
def r_mca_tea() -> dict:
    return _load_r_fixture("mca", "tea")


@pytest.fixture(scope="session")
def r_mca_tea_burt() -> dict:
    return _load_r_fixture("mca", "tea_burt")


@pytest.fixture(scope="session")
def r_famd_poison() -> dict:
    return _load_r_fixture("famd", "poison")


@pytest.fixture(scope="session")
def r_famd_poison_sup() -> dict:
    return _load_r_fixture("famd", "poison_sup")


@pytest.fixture(scope="session")
def r_mfa_poison() -> dict:
    return _load_r_fixture("mfa", "poison")


@pytest.fixture(scope="session")
def r_hmfa_poison() -> dict:
    return _load_r_fixture("hmfa", "poison")


@pytest.fixture(scope="session")
def r_hmfa_decathlon() -> dict:
    return _load_r_fixture("hmfa", "decathlon")


@pytest.fixture(scope="session")
def r_dmfa_decathlon() -> dict:
    return _load_r_fixture("dmfa", "decathlon")


@pytest.fixture(scope="session")
def r_plot_ellipse_decathlon() -> dict:
    return _load_r_fixture("plot", "ellipse_decathlon")


@pytest.fixture(scope="session")
def r_gpa_synth() -> dict:
    return _load_r_fixture("gpa", "synth")


@pytest.fixture(scope="session")
def r_gpa_synth_uneven() -> dict:
    return _load_r_fixture("gpa", "synth_uneven")


@pytest.fixture(scope="session")
def r_hcpc_decathlon() -> dict:
    return _load_r_fixture("hcpc", "decathlon_plain_k4")


@pytest.fixture(scope="session")
def r_dimdesc_pca_decathlon() -> dict:
    return _load_r_fixture("dimdesc", "pca_decathlon")


@pytest.fixture(scope="session")
def r_dimdesc_ca_children() -> dict:
    return _load_r_fixture("dimdesc", "ca_children")


@pytest.fixture(scope="session")
def r_dimdesc_mca_tea() -> dict:
    return _load_r_fixture("dimdesc", "mca_tea")


@pytest.fixture(scope="session")
def r_catdes_tea() -> dict:
    return _load_r_fixture("catdes", "tea_Tea")


@pytest.fixture(scope="session")
def r_condes_decathlon() -> dict:
    return _load_r_fixture("condes", "decathlon_Points")


@pytest.fixture(scope="session")
def r_condes_tea_age() -> dict:
    return _load_r_fixture("condes", "tea_age")


@pytest.fixture(scope="session")
def r_dimdesc_pca_decathlon_proba50() -> dict:
    return _load_r_fixture("dimdesc", "pca_decathlon_proba50")
