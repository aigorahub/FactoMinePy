"""Deferred-method stubs.

Importable so ``from factominer import DMFA`` works, but raising
``NotImplementedError`` when called. Each stub points at the plan that records
the round-2 work and the reason.
"""

from __future__ import annotations

from typing import Any


def _deferred(name: str, hint: str) -> Any:
    def stub(*_args: Any, **_kwargs: Any) -> Any:
        raise NotImplementedError(
            f"{name} is not yet implemented. {hint} "
            f"See ROADMAP.md and the README supported-methods table for the "
            f"current status."
        )

    stub.__name__ = name
    stub.__qualname__ = name
    stub.__doc__ = f"Stub for {name}; deferred to Round 2."
    return stub


DMFA = _deferred(
    "DMFA",
    "Dual Multiple Factor Analysis is planned for the next iteration.",
)
