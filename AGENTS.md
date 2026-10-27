# Repository agent guide

## Mandatory MolSysSuite instructions

Read and follow `MOLSYSSUITE_GUIDE.md` before working in this repository.

Within their stated scope, its common rules take precedence over this file
and any nested `AGENTS.md`. Local instructions may refine them; deviations
require the documented policy exception process.

The synchronized guide is owned by `uibcdf/molsyssuite`. It includes the
[reusable-tool ownership rules](MOLSYSSUITE_GUIDE.md#modular-reusable-tools)
and [working-instruction rules](MOLSYSSUITE_GUIDE.md#durable-working-instructions).
For work under `devguide/`, also read `devguide/AGENTS.md` and its local
reporting protocol. Keep repository-specific instructions below.

## External Tooling Guides (Required for Development)

These guides are required reading for anyone developing this library. They describe how
external tools must be used here.

- `GH_RUN_RECEPTOR_GUIDE.md` — Required guide for compact, truth-preserving inspection of
  GitHub Actions runs and the native-command fallback.
- `ACKREDIT_GUIDE.md` — Required guide for optional scientific attribution and citation
  reporting.
- `MOLSYSSUITE_GUIDE.md` — Required suite-governance guide; this synchronized copy must
  not be edited locally.

## Local reporting and policy caller

Use `devguide/reporting_protocol.md` for this repository's actual queue/archive
paths and `python devtools/devguide_index.py --check` for index checks. The local
reporting test command is `python -m unittest discover -s tests -p test_reporting_protocol.py`.
The frozen Python-policy caller remains `.github/workflows/molsyssuite-policy.yml`;
retain its reviewed pin and the separate current-guide/instruction audit.

## Molecular-system ownership

Use supported public MolSysMT operations for molecular-system conversion,
selection, topology and coordinate access/updates, extraction, and structure
assembly. ElastNetMT owns ENM definitions, numerical matrices, spectra and
model-specific displacements; pass their molecular results to MolSysMT for
system construction/manipulation. Extend or request missing molecular tools in
MolSysMT rather than copying its implementation or accessing private structures.

For MolSysViewer add-on inputs, use public `view.molsys`, which supplies the
normalized `molsysmt.MolSys`. Keep explicit alternate input forms supported
through public MolSysMT conversion.

## Component qualification

Track this member's source qualification and public-delivery evidence in
`uibcdf/elastnetmt#19`. The common Python/support
requirements and actual component metadata retain their separate authority.

## Registered integration guides

Read the registered consumer guides when working on their respective boundaries:

- `SMONITOR_GUIDE.md`
- `DEPDIGEST_GUIDE.md`
- `ARGDIGEST_GUIDE.md`
- `PYUNITWIZARD_GUIDE.md`
