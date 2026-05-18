# Security policy

FactoMinePy is a numerical / statistical library. It does not accept network
input, parse untrusted file formats beyond what pandas / numpy do, or execute
user-supplied code. The realistic attack surface is small: an unsafe
deserialization in pandas / numpy could in principle propagate through a
`load_*` helper that reads a bundled CSV, but those CSVs are static and
committed to the repository.

## Supported versions

The package is pre-1.0 and tracks current FactoMineR releases. Security and
correctness fixes land on `main`; we do not maintain backports.

| Version | Supported |
| --- | --- |
| 0.1.x (current) | ✅ |
| < 0.1 | ❌ (pre-release) |

## Reporting a vulnerability

If you find a security issue, please **do not** open a public GitHub issue.
Instead:

1. Email `hello@aigora.com` with a subject line starting `[security] FactoMinePy:`
   and a minimal reproducer.
2. We aim to acknowledge within 5 business days and to provide a fix or a
   mitigation timeline within 30 days.

For non-security correctness issues (numerical disagreement with R FactoMineR,
test failures, ergonomic problems), open a regular GitHub issue.
