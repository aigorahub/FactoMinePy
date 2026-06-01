"""factominer — a Python port of R's FactoMineR.

This module re-exports the public API. The supported-methods table in
``README.md`` is the source of truth for which symbols are live and which are
stubs that raise ``NotImplementedError``.
"""

from __future__ import annotations

from ._result import Result
from .ca import CA
from .desc import catdes, condes, dimdesc
from .dmfa import DMFA
from .famd import FAMD
from .gpa import GPA
from .hcpc import HCPC
from .hmfa import HMFA
from .mca import MCA
from .mfa import MFA
from .pca import PCA
from .predict import predict
from .reconst import estim_ncp, reconst

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
    "predict",
    "reconst",
    "estim_ncp",
    "Result",
]

__version__ = "0.2.0.dev0"
