"""Bundled datasets re-used from FactoMineR's distribution for parity testing.

See ``factominer/datasets/data/PROVENANCE.md`` for the origin and licensing of
each file.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

_DATA_DIR = Path(__file__).parent / "data"


def _load_csv(name: str) -> pd.DataFrame:
    path = _DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"dataset not bundled: {path.name}")
    return pd.read_csv(path, index_col=0)


def load_decathlon() -> pd.DataFrame:
    """41 athletes × 13 columns from the 2004 Athens Olympic + Décastar decathlons.

    Columns: ten athletic events (seconds or meters), plus ``Rank``, ``Points``,
    and ``Competition`` (a two-level factor). FactoMineR's canonical PCA example.
    """
    return _load_csv("decathlon.csv")


def load_children() -> pd.DataFrame:
    """18 × 8 contingency table on the perceptions of children's worries.

    Rows: kinds of worries. Columns: socio-educational categories. Used in
    FactoMineR's CA examples.
    """
    return _load_csv("children.csv")


def load_tea() -> pd.DataFrame:
    """300 × 36 survey on tea consumption habits.

    Mostly categorical (factors); one integer column. Canonical MCA example.
    """
    return _load_csv("tea.csv")


def load_poison() -> pd.DataFrame:
    """55 × 15 food-poisoning outbreak survey.

    Mixed categorical + quantitative. Used in MCA / FAMD examples.
    """
    return _load_csv("poison.csv")
