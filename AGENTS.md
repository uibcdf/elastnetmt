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
`uibcdf/molsyssuite`; keep ElastNetMT product
work and local issues in this repository. The root `MOLSYSSUITE_GUIDE.md` is a
synchronized read-only copy.

For bugs and proposals, open the local GitHub issue before adding a report.
Follow `devguide/reporting_protocol.md`, use `devguide/templates/report.md`,
and run `python devtools/devguide_index.py --check` plus
`python -m unittest discover -s tests -p test_reporting_protocol.py` before
committing. The pending queues and permanent archive have generated indexes.

## Modular reusable tools

Before adding a feature, inspect existing tools and identify the owning module or
component. Implement or extend independently useful operations as documented reusable
tools in that owner, with their own contracts and tests; have consumers call them.
Keep task-specific decisions local and report missing sibling capabilities to the
provider with linked consumer evidence. Follow
[MOLSYSSUITE_GUIDE.md#modular-reusable-tools](MOLSYSSUITE_GUIDE.md#modular-reusable-tools)
for applicability, compatibility, performance and tracked exceptions.

## Molecular-system ownership

Use supported public MolSysMT operations for molecular-system conversion,
selection, topology and coordinate access/updates, extraction, and structure
assembly. ElastNetMT owns ENM definitions, numerical matrices, spectra and
model-specific displacements; pass their molecular results to MolSysMT for
system construction/manipulation. Extend or request missing molecular tools in
MolSysMT rather than copying its implementation or accessing private structures.

## Durable working instructions

Keep technical findings in owning issues, fixes, tests and maintained guidance.
Place only accepted lasting contributor actions in root or appropriately scoped
instructions, following
[the common policy](MOLSYSSUITE_GUIDE.md#durable-working-instructions).
For work under `devguide/`, also read [devguide/AGENTS.md](devguide/AGENTS.md)
and its local reporting protocol. Shared instruction proposals belong in
`uibcdf/molsyssuite`; cross-MOLI contracts belong in `uibcdf/moli`.


## Required Python support

The required source contract is Python 3.11–3.14; routine development uses
Python 3.14. Qualification and public delivery are tracked in `uibcdf/elastnetmt#19`.
Keep metadata, recipe, required CI and recovery evidence aligned. Normal
installed evidence must not bypass `Requires-Python`; public support claims
remain tied to the suite's recorded admission.

## Human-facing issue feedback

Surface actionable suspected defects, inconsistencies, missing analyses and
improvements, including uncertain or nonblocking findings. When working with a
human, offer an owning issue at a natural pause; retain existing reporting
authorization and respect declined/deferred disclosure. Follow
[the accepted feedback route](MOLSYSSUITE_GUIDE.md#human-facing-issue-feedback)
for ownership, uncertainty, privacy and exceptions.
