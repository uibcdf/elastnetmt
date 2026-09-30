---
summary: Complete contributor full-CI routes and skipped-push recovery.
issue: uibcdf/elastnetmt#17
status: partial
opened: 2026-09-30
closed:
severity: medium
verification: measured
area: [governance, ci]
guard: tests/test_ci_backlog.py
normative:
blocked_by: []
supersedes: []
---

# Full-CI contributor routes and skipped-push recovery

## What

Implement uibcdf/molsyssuite#39 in ElastNetMT. At source 82905a8, main has basic
protection without an explicit PR rule or required status checks. Complete
push/PR and weekly/manual CI already cover Python 3.11–3.13 on Linux/macOS,
with independent reporting and a separate MolSysViewer add-on contract.
Conditional recovery for authorized internal skipped pushes is missing.

## How

Preserve unfiltered complete collection, minor-specific Conda environments
and controlled suite source revisions. Preserve the tested MolSysMT source
replacement only for Python 3.13; Python 3.11/3.12 retain their existing
Conda source. Keep the full plain pytest scientific command and its existing
Pytest Receptor adoption gap separately under uibcdf/elastnetmt#14.
Pin macOS to macos-15 and assert arm64 and each Python minor before tests.
Keep independent Reporting governance's standard-library report validation
and add administrative CI guards with published pip pytest-receptor 1.0.0.
These tools do not alter scientific Conda pins or scientific test selection.

Retain unconditional weekly Monday 09:00 UTC/manual complete execution and
the existing unfiltered MolSysViewer contract. Add daily conditional recovery
at 02:19 America/Mexico_City and a typed probe_backlog=true dispatch without
heavy matrix jobs. Uncertain history/API or failed decision jobs run full
coverage. Require explicit PRs with zero mandatory approvals and nine strict
checks: Reporting governance, policy / conformance (including Ruff), all six
supported test jobs, and the existing add-on contract check. Current admins
dprada/LMMV retain direct pushes; isandom's existing maintain role is preserved
and uses the PR route. No repository access is changed.

A full watermark requires a successful ancestral main push/schedule/manual
CI run with all three Linux minors and actual successful Run tests steps.
Probes, failures, PRs, other branches and skipped test steps cannot clear
skipped-commit debt. The detector filters main locally from unfiltered API
listings; unpaid debt survives ordinary commits and calendar boundaries.

## Why

External integration requires the complete supported suite while internal
iteration remains lightweight through direct pushes and skip-CI. Governance
must remain testable during early development and actual scientific failures
must remain visible without being mistaken for successful complete coverage.

## What is measured and what is assumed

On 2026-09-30, fresh protection API lacks both required_status_checks and
required_pull_request_reviews; existing administrators are exempt. Collaborator
API lists dprada/LMMV as admin and isandom as maintain. Weekly CI 36459131786
at 9566707 passed Reporting governance and both Python 3.13 test jobs, but
failed the four actual Python 3.11/3.12 test jobs. Native Linux 3.11 logs
confirm test_anm_trajectory_generation raises the known LinDelINT auto-engine
ImportError requiring CuPy. This provider debt is already in
uibcdf/elastnetmt#14 and uibcdf/lindelint#8. MolSysViewer contract 36460440355
and policy 36357927792 passed. The new route guard first failed against the
old workflow_dispatch configuration with no probe input.

## Alternatives and refuted paths

Scientific failures cannot become cleared debt through successful governance
probes. Looking only at today's skipped commits would lose earlier unpaid
skips. Weakening collection, tolerating failures or changing MolSysMT sources
across minors would hide component-specific evidence. Existing full routine
CI needs no new bounded-smoke exception.

## Scope and exclusions

CI routing, administrative guards, architecture evidence, protection and
reporting only. Scientific implementation, assertion/source/environment pins,
release/platform claims and support range remain unchanged. Ecosystem work
and its Pytest Receptor uniformity gap remain uibcdf/elastnetmt#14; provider
fallback remains uibcdf/lindelint#8. Core MolSysMT/MolSysViewer science reviews
are deferred at the user's direction.

## Acceptance criteria

- Verify explicit PRs, strict checks and named administrator bypass.
- Execute independent hosted governance/probes and retain debt after skips.
- Dispatch complete six-cell CI and preserve actual scientific outcomes.
- Retain the specialized MolSysViewer contract and its own test selection.
- Observe actual daily recovery and hosted external PR before final adoption.
- Review installed-artifact/publication-platform claims separately.
- Retain tests/test_ci_backlog.py and devtools/tests/test_ci_routes.py as durable guards.

## Provenance

2026-09-30; isolated clone based on 82905a8, preserving original worktrees.
Python 3.13.15; GH Run Receptor 1.0.0 preserves the failed weekly baseline;
native job/step/log evidence supplies the observations above. New execution
and protection evidence are recorded below after publication.

## Local implementation verification

Eight administrative tests passed with pytest-receptor llm; the required
standard-library reporting invocation also passed three tests. Ruff lint and
formatting passed for all 59 files, reporting indexes are current and central
component conformance passes. The route regression failed before the recovery
input existed and passed after implementation. The component scientific
pytest command, minor-specific MolSysMT sources, source revision file, Conda
environments and specialized contract workflow are unchanged.

## Hosted governance and first backlog evidence

Source c68f662 was published through the authorized internal skip-CI route.
GitHub reported bypass of the explicit PR rule and all nine required checks.
Protection API confirms strict status checks, zero mandatory approvals,
administrator exemption and no force/deletion. Existing isandom maintain
access is unchanged; only the administrators have the direct-push bypass.

Probe [36775315293](https://github.com/uibcdf/elastnetmt/actions/runs/36775315293)
passed actual reporting/index and CI-governance steps plus the detector.
It recognized the older executed full a47c067 watermark and found five
pending skipped commits, including the guide distribution and implementation.
Heavy jobs were omitted. Successful administrative execution did not clear
these skips, and the newer failed scientific matrices were not anchors.
Suite policy (including Ruff)
[36775320115](https://github.com/uibcdf/elastnetmt/actions/runs/36775320115)
passed at the same source. Specialized add-on contract
[36775325575](https://github.com/uibcdf/elastnetmt/actions/runs/36775325575)
was dispatched; its actual result remains to be recorded.

The issue and review stay partial. Complete manual execution and a subsequent
probe will verify debt on the published record revision; their evidence belongs
in the owning issue and central adoption record. Actual daily execution,
hosted external PR and installed-artifact/platform claims remain unreviewed.
Scientific failures cannot become a cleared debt through governance success.

## Administrative collection regression and correction

Manual complete CI 36775597556 at 3d2c59b passed both Python 3.13 scientific
cells and independent governance, but the four older-minor jobs failed during
collection: the new YAML route guard imported PyYAML, absent from their
existing scientific environments. This is a local governance implementation
regression under #17, not the pre-existing LinDelINT scientific failure.
GH Run Receptor and native collection logs preserve ModuleNotFoundError for
yaml; do not attribute this run's four failures to the provider.

Move the administrative-only YAML guard to devtools/tests/test_ci_routes.py
and select it explicitly in independent governance, whose bootstrap already
installs PyYAML. Existing pytest testpaths=["tests"] keeps the new administrative
dependency outside scientific collection. The scientific command, environments,
source pins, existing test modules and their selection remain intact; no test
is skipped. The standard-library backlog tests remain in scientific tests.
Repeat complete CI on the corrected source to verify collection is restored,
and retain the failed first manual run as regression evidence. This local
correction adds no common tool dependency to scientific environments.
