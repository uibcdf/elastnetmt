---
summary: Adopt the mandatory four-minor contract and qualify normal installed delivery
issue: uibcdf/elastnetmt#19
status: partial
opened: 2026-10-03
closed:
verification: inspected
area: [compatibility, packaging, ci, governance]
guard:
normative:
blocked_by: []
supersedes: []
---

# Required Python 3.14 adoption

## What

The suite maintainer requires Python 3.11–3.14 from every Python member under
uibcdf/molsyssuite#51 and immutable `policy-v1.5.3`. Inspected source `e1c560621a54e32cd23741813cfdc477298203fe`
still excluded 3.14. This record separates required adoption from scientific
qualification and public delivery.

## How

Metadata, contributor instructions, required full CI, applicable recipe and
installed-candidate matrices now cover `>=3.11,<3.15`. Routine development
stays on 3.13. Recovery requires successful **executed** Linux full tests on
all four minors before advancing its watermark. PR/internal-push schedules
and all existing scientific assertions/test selection are preserved.

The new 3.14 lane uses the existing controlled-source mechanism, with MolSysMT
`3eb5afd1de087f775b78d7fa45ad69cca3a02d43` and MolSysViewer `ec4c71e574d798b7c8675b7e7e983da878ce9889` (metadata inspected to admit 3.14;
the suite transition records their qualified source pair). Older minors keep
their prior source revisions. Where needed, the 3.14 environment keeps the
3.13 scientific dependency surface and uses published Pytest Receptor 1.1.0.
ElastNetMT's LinDelINT provider migration is owned by uibcdf/lindelint#14.
These source routes remain test evidence, not publicly delivered closure;
replace them after reviewed compatible public packages are independently
installed. Do not bypass Requires-Python.

## Why

Old provider revisions cap Python below 3.14, so changing only the consumer
bound would leave ordinary installation blocked. A three-minor matrix must
not clear the new required four-minor CI debt.

## What is measured and what is assumed

Source metadata, exact provider bounds, existing CI and prior recipe/resource
gates have been inspected. New solver, installation and full-test outcomes
are recorded as obtained; configuration alone proves none of them.

## Alternatives and refuted paths

Metadata overrides and tolerated/skipped scientific failures cannot establish
support. Replacing older-minor dependency generations globally would expand
the compatibility surface unnecessarily; the new route is scoped to 3.14.

## Scope and exclusions

Governance and ecosystem compatibility only. Scientific defects remain with
the owning component team and are neither suppressed nor fixed here. Source
configuration does not authorize public upload or a delivered-support badge.

## Acceptance criteria

- Coherent four-minor metadata/recipe/full-CI/installed-artifact contract.
- Ordinary installed 3.14 import and full relevant tests, or concrete owned
  blockers that preserve actual failure and bounded pending adoption.
- Historical three-minor evidence cannot clear skipped-CI debt.
- Candidate/channel and fresh public clean-install evidence precede admission.

The recovery regression is
`tests/test_ci_backlog.py::test_a_previous_three_minor_matrix_cannot_clear_314_debt`.

### Test-results publisher condition inspected on 2026-10-03

Expanding the matrix exposed an existing malformed mixed expression in the
test-results upload condition. Actionlint reported that surrounding text made the
condition always true. The complete condition is now one GitHub expression,
retaining test-results publication only from Linux/Python 3.13 after failed tests
as well as successful tests, unless the run is cancelled. Python 3.14 cells
run the suite without publishing additional test-results uploads. The separate
coverage report publisher was already correctly scoped to Linux/Python 3.13.

### First hosted results and administrative corrections — 2026-10-03

The first hosted run 37105616453 reproduced one stale administrative
expectation of the previous three-minor matrix in
`devtools/tests/test_ci_routes.py`. The guard now covers all four minors and
the existing 3.13 / new 3.14 environment selection. All four 3.13/3.14
scientific jobs passed; the unchanged 3.11/3.12 lanes failed in
`tests/integration/test_anm_trajectory.py::test_anm_trajectory_generation`.
Those scientific results remain visible for the component team.

### Qualification checkpoint — 2026-10-03

Source `062d6347a142476067ffdb86c06c6cfd9478e51a`: [CI run 37106324494](https://github.com/uibcdf/elastnetmt/actions/runs/37106324494).
Reporting governance passes. All four 3.13/3.14 scientific cells pass; the
four 3.11/3.12 cells retain the known trajectory-generation failures tracked
by uibcdf/elastnetmt#14/#17. No failing matrix is accepted as a recovery
watermark. Public noarch delivery remains under uibcdf/elastnetmt#18.

Main now retains strict PR protection with 11 checks, adding Linux and
macOS ARM Python 3.14 to the prior checks. Existing administrator bypass for
internal direct pushes is preserved. Source feasibility is recorded centrally
as `authorized`, not public `admitted` support; the badge remains unchanged.
A documentary skipped push must remain visible to nightly recovery.

## Routine policy 1.5.4 adoption — 2026-10-03

The maintainer authorized publication and adoption of policy-v1.5.4 under
uibcdf/molsyssuite#39. The immutable tag points to central e459ea0; the
component now calls that published gate and receives the byte-identical
canonical guide through the suite synchronizer. Routine development uses
Python 3.14. The existing full Python 3.11–3.14 matrices and skipped-commit
recovery semantics are preserved; no public package is published here.
Local conformance and changed-workflow Actionlint checks pass. Hosted
policy and applicable routine checks are dispatched separately from skipped
direct pushes; their exact commits and outcomes remain to be measured.

The independent reporting/governance interpreter moves to 3.14. Complete
scientific matrices already contain 3.14; coverage-only publication retains
its existing measured 3.13 lane. A configured development environment is
not fresh installed-artifact or public-channel qualification. Scientific
failures and remaining distribution gates remain owned by their existing issues.



## Installed cache CI follow-up, 2026-10-10

Actual installed CI at c7d85a2 (run 38053683540) exposed a missing Viewer
bootstrap on 3.13 and 16 cache failures on 3.14 with old MolSysMT 3eb5afd1.
The former does not qualify complete scientific collection; the latter ran
218 tests with 202 passes, so earlier successful local evidence with a newer
molecular provider could not qualify the older pinned source context.

All source scientific minors now select MolSysMT
8ae160fc93ed5bc815bcc24b37c2875ba735623d, containing the owner fixes for empty
native connectivity (#283) and undefined comparison metadata (#345), together
with the previously selected Viewer ec4c71e574d798b7c8675b7e7e983da878ce9889.
Both metadata contracts admit 3.11–3.14. Add-on dependencies are explicit test
scope, the generated ordinary test/development environments are synchronized,
and fixed-source SDK preflight verifies actual installation before science.
A source-context guard requires both providers in every minor. Keep #19 open
until hosted and original native Conda/public evidence is complete.


The selected molecular provider requires PyUnitWizard >=0.28.1; its old
controlled source c7a9ff0 installed version 0.26.0+13 and cannot satisfy that
contract. Use qualified release source 25a4bc2468da4ef3af2a638c0bf068becf2acfb4
(PyUnitWizard 0.28.1). That release requires ArgDigest >=0.14.0, so use its
qualified 0.14.0 source 0fa776af2d271065c60727c28480b20c3ce09aee instead of
c604ce3 (installed 0.13.0+13). Existing DepDigest 0.11.0+13 and SMonitor
0.16.0+20 source versions satisfy these selected floors. This is a reviewed
source bootstrap correction, not a public Conda dependency-closure claim.


The final local source probe selects exact Viewer ec4c71e5, PyUnitWizard
25a4bc24 and ArgDigest 0fa776af Python code in a task-owned temporary path,
with the primary corrected MolSysMT Python/native context and remaining
primary dependencies. All 218 tests pass without skips (68.72 s). This proves
those scientific source APIs together; it is not a normally installed
selected-provider matrix or Conda qualification. All 61 administrative guards
also pass (24 CI/native, 10 source routes, 10 distribution, 14 environment,
3 reporting), together with Ruff, indexes, environment generation and suite
conformance. Subsequent hosted qualification remains necessary for every
supported interpreter/platform and original package bytes.
