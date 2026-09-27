---
summary: Adopt the MolSysSuite issue-backed reporting lifecycle locally.
issue: uibcdf/elastnetmt#16
status: resolved
opened: 2026-09-27
closed: 2026-09-27
verification: inspected
area: [governance, reporting]
guard: tests/test_reporting_protocol.py::TestReportingProtocol::test_existing_reports_have_valid_metadata_and_generated_indexes
normative:
blocked_by: []
supersedes: []
---

# Adopt the reporting lifecycle

## What

Provide the local bug queue, permanent archive, report template, generated
indexes, offline validator and independent governance CI job required by
`uibcdf/molsyssuite#60`.

## How

Preserve the active policy review `uibcdf/elastnetmt#14` and generate its
proposal index. Add a stdlib-only validator and test it with negative metadata
and guard-selector cases. Run the check in a job independent of the scientific
matrix.

## Why

The current developer guide has a manual proposal list but lacks the common
bug and archive surfaces. A missing issue, stale index, false closure or
nonexistent guard can be committed without an offline governance failure.

## What is measured and what is assumed

Inspection of `main` on 2026-09-27 found one issue-backed active proposal,
but no local bug queue, archive, report template, generated index, offline
validator or reporting CI job.

## Scope and exclusions

This change governs report records. It does not modify scientific tests,
package dependencies, or the separate Python CI-lane rollout.

## Acceptance criteria

The validator accepts the existing active proposal and rejects missing issue
identity, false closure and unresolvable pytest selectors. Generated indexes
are current. The governance job passes on the published commit independently
of the scientific matrix. Close the local issue with the durable guard and
archived report path.

## Resolution

Commit `9ecc8f0` added the bug queue, permanent archive, report template,
offline validator, generated indexes and independent governance job. The
guard checks the issue-backed reports and current generated indexes; the
additional negative tests reject false closure and unresolvable selectors.
Local reporting tests and Ruff checks passed. Hosted CI run `36357880305`
passed its independent Reporting governance job, and MolSysSuite policy run
`36357880758` passed. Scientific and add-on jobs are separate from this
reporting outcome.
