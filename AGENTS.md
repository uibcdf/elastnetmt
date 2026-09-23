# Repository agent guide

## External Tooling Guides (Required for Development)

These guides are required reading for anyone developing this library. They describe how
external tools must be used here.

- `GH_RUN_RECEPTOR_GUIDE.md` — Required guide for compact, truth-preserving inspection of
  GitHub Actions runs and the native-command fallback.
- `ACKREDIT_GUIDE.md` — Required guide for optional scientific attribution and citation
  reporting.
- `MOLSYSSUITE_GUIDE.md` — Required suite-governance guide; this synchronized copy must
  not be edited locally.

## MolSysSuite coordination

Route shared Python, CI, Ruff, release, and integration policy through
`uibcdf/molsyssuite` and the inherited MOLI baseline; keep ElastNetMT product
work and local issues in this repository. The root `MOLSYSSUITE_GUIDE.md` is a
synchronized read-only copy.
