<!-- Thanks for the contribution! Keep the description focused — what changed
     and why. The "why" matters more than the "what"; the diff already shows
     the latter. -->

## Summary

<!-- 1-3 bullet points. -->

## R FactoMineR parity

<!-- For numerical changes: which R FactoMineR function / version did you
     compare against, and at what tolerance? Cite line numbers in
     husson/FactoMineR/R/<file>.r where relevant. -->

## Test plan

- [ ] `ruff check factominer tests` clean
- [ ] `pytest -q` passes
- [ ] If the change is numerical: `rpy2-parity` CI run dispatched and green
      (link the run)
- [ ] Sphinx build clean: `python -m sphinx -W -b html docs docs/_build/html`
