---
name: Bug report
about: A numerical disagreement with R FactoMineR, a crash, or unexpected behavior
title: ""
labels: bug
assignees: ""
---

## What's wrong

<!-- One or two sentences. -->

## Minimal reproducer

```python
# Python code that produces the bug. Use a bundled dataset
# (load_decathlon, load_children, load_tea, load_poison) when possible
# so anyone can run this without sourcing data.
```

## Expected vs actual

- **Expected:** <!-- what R FactoMineR produces, or what the docs claim -->
- **Actual:** <!-- what you got -->

## Versions

- FactoMinePy: <!-- pip show factominer | grep Version -->
- Python: <!-- python --version -->
- numpy / pandas / scipy: <!-- pip show numpy pandas scipy | grep Version -->
- OS / arch: <!-- macOS 14 arm64 / Ubuntu 24.04 x86_64 / etc. -->

## R-side reproducer (if the bug is a parity issue)

```r
# R FactoMineR call that produces the expected output. Include
# R --version and packageVersion("FactoMineR").
```
