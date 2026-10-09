---
summary: Correct GNM calibration, plotting and the final cutoff-search state.
issue: uibcdf/elastnetmt#21
status: active
opened: 2026-10-08
closed:
severity: high
verification: measured
area: [physics, units]
guard: tests/physical/test_gnm_calibration.py
normative:
blocked_by: []
supersedes: []
---

# GNM B-factor calibration

## What

Fitting reused already scaled predictions, so a second fit changed the scale
to one. Plotting multiplied a scaled curve again. Cutoff search restored the
winning contacts but retained the last candidate's calibration. Experimental
B factors lacked an explicit square-angstrom conversion boundary.

## How

Separate the raw pseudoinverse diagonal from its public scaled prediction.
Fit raw values against experimental square-angstrom magnitudes, fit before
plotting, reset calibration with contacts, and refit the winning cutoff.

## Why

The bugs change observable predictions depending on call order and unit
policy, even though the molecular system and intended model are unchanged.

## What is measured and what is assumed

The new calibration and import-policy regression tests failed against the
initial implementation and passed after correction on Python 3.14.7.
The deterministic eight-node PDB fixture supplies known experimental B
factors; the installed MolSysMT TcTIM PDB supplies the scientific reference.
Full hosted qualification is recorded separately after execution. No public
installed-artifact admission is inferred from source tests.

## Alternatives and refuted paths

Resetting the scale before each fit leaves plot and cutoff-state errors
unprotected. Adapting only the plot would hide the unstable numerical API.

## Scope and exclusions

GNM calibration and call-order/unit regressions only. Provider fallback is
uibcdf/lindelint#8; ecosystem adoption remains #14; public distribution and
Python admission remain #18/#19. Degenerate networks and missing or constant
experimental profiles require a separate scientific contract review.

## Acceptance criteria

Repeat fitting gives the same scale and prediction, plotting agrees with the
public prediction whether already fitted or not, cutoff search returns a
model equivalent to a fresh fit at the selected cutoff, and equivalent
unit policies give identical square-angstrom predictions. The guard contains
assertions for each mechanism. Integration and merge remain pending.

## Implementation evidence — 2026-10-09

[PR #22](https://github.com/uibcdf/elastnetmt/pull/22) contains the correction
and durable guards. The local complete suite passed 71 tests on Python
3.14.7, including the unfitted plot's dimensionless label; the developer-tool,
reporting, Ruff and central conformance checks also passed. Hosted workflow
outcomes and their exact revisions belong in that PR's qualification record.
The issue remains open until integration; this report does not assert public
installed delivery or completion of the wider modernization roadmap.
