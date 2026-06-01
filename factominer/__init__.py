"""factominer — a Python port of R's FactoMineR.

This module re-exports the public API. The supported-methods table in
``README.md`` is the source of truth for which symbols are live and which are
stubs that raise ``NotImplementedError``.
"""

from __future__ import annotations

# Deferred methods. Imported so ``from factominer import HMFA`` works,
# but the implementations raise NotImplementedError when called.
from ._deferred import DMFA, HMFA
from ._result import Result
from .ca import CA
from .desc import catdes, condes, dimdesc
from .famd import FAMD
from .gpa import GPA
from .hcpc import HCPC
from .mca import MCA
from .mfa import MFA
from .pca import PCA

__all__ = [
    "PCA",
    "CA",
    "MCA",
    "FAMD",
    "MFA",
    "HMFA",
    "DMFA",
    "GPA",
    "HCPC",
    "dimdesc",
    "catdes",
    "condes",
    "Result",
]

__version__ = "0.2.0.dev0"
