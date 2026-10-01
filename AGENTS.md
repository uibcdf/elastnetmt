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
