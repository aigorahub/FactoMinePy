"""Deferred-method stubs.

Importable so ``from factominer import HMFA`` works, but raising
``NotImplementedError`` when called. Each stub points at the plan that records
the round-2 work and the reason.
"""

from __future__ import annotations

from typing import Any


def _deferred(name: str, hint: str) -> Any:
    def stub(*_args: Any, **_kwargs: Any) -> Any:
        raise NotImplementedError(
            f"{name} is a Round 2 deferral. {hint} "
            f"See docs/plans/factominer-python-port.md §2 and the README "
            f"supported-methods table for the current status."
        )

    stub.__name__ = name
    stub.__qualname__ = name
    stub.__doc__ = f"Stub for {name}; deferred to Round 2."
    return stub


FAMD = _deferred(
    "FAMD",
    "Factor Analysis for Mixed Data is planned for the next iteration.",
)
MFA = _deferred(
    "MFA",
    "Multiple Factor Analysis is planned for the next iteration.",
)
HMFA = _deferred(
    "HMFA",
    "Hierarchical Multiple Factor Analysis is planned for the next iteration.",
)
DMFA = _deferred(
    "DMFA",
    "Dual Multiple Factor Analysis is planned for the next iteration.",
)
GPA = _deferred(
    "GPA",
    "Generalized Procrustes Analysis is planned for the next iteration.",
)
