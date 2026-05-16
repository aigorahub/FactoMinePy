# Dataset Provenance

The bundled CSVs under this directory are re-extracted from the R FactoMineR
package's built-in data exports for parity-testing purposes. The underlying
data are publicly documented in the FactoMineR textbooks and published
sources cited below.

## decathlon.csv

- **Origin.** Performances and final standings of decathletes at the 2004 Athens
  Olympic Games (Athletissima) and at the 2004 Décastar (Talence, France).
- **Primary source.** Published athletics results; cf. Husson, Lê, Pagès,
  *Exploratory Multivariate Analysis by Example Using R* (2nd ed., 2017),
  Chapter 1. The IAAF / World Athletics archives hold the same final standings.
- **Shape.** 41 rows × 13 columns. Ten event measurements (seconds or meters),
  ``Rank``, ``Points``, ``Competition`` (Decastar / OlympicG).
- **Licensing.** The data themselves are publicly reported athletic results.
  The exact tabulation distributed with FactoMineR is GPL-licensed. This copy
  is provided for parity-testing convenience; if you need a license-clean
  bundle, re-derive from the IAAF source.

## children.csv

- **Origin.** Survey on the perceptions of children's worries by
  socio-educational category. Published in the FactoMineR textbook
  (Husson, Lê, Pagès 2017), Chapter 4.
- **Shape.** 18 rows × 8 columns. Contingency table of counts.
- **Licensing.** Same notice as decathlon.

## tea.csv

- **Origin.** Survey of 300 people on their tea consumption habits, used as the
  canonical MCA example in FactoMineR. Husson, Lê, Pagès 2017, Chapter 4.
- **Shape.** 300 rows × 36 columns. Mostly factor variables, one integer
  (``age``).
- **Licensing.** Same notice as decathlon.

## poison.csv

- **Origin.** Food-poisoning outbreak survey, FactoMineR Chapter 4.
- **Shape.** 55 rows × 15 columns. Mixed quantitative + categorical.
- **Licensing.** Same notice as decathlon.

## On licensing

All code in this package is MIT. The bundled CSV data above are convenience
copies of the FactoMineR distribution's datasets, used here to validate
numerical parity with the R implementation. Each underlying dataset has a
publicly documented primary source; if redistribution under a non-GPL license
is required, re-derive each from its primary source rather than reusing these
copies.
