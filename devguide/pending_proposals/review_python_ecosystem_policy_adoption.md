---
summary: Review ElastNetMT Python ecosystem policy adoption.
issue: uibcdf/elastnetmt#14
status: active
opened: 2026-09-27
closed:
verification: measured
area: [governance, tooling]
guard:
normative:
blocked_by: [uibcdf/lindelint#8]
supersedes: []
---

# Review Python ecosystem policy adoption

**Reported:** 2026-09-27 under `uibcdf/molsyssuite#56`; inspected
`6705363187762a69048d147853f1018097c76a5e` on `origin/main`.

## What

Both support-library and developer-tool adoption are **partial**. The package
uses the four suite support libraries, but has a process-wide unit-policy
override and a failing interpolation integration. Its maintained CI does not
yet use Pytest Receptor consistently.

## How

`pyproject.toml` declares ArgDigest, DepDigest, SMonitor, and PyUnitWizard.
Model paths use ArgDigest contracts, optional dependency checks, structured
signals, and quantities. `_pyunitwizard.py` unconditionally selects shared
defaults during import; test that a user-selected policy survives import.

Hosted CI run `36311638612` at this source failed four of six cells in
`tests/integration/test_anm_trajectory.py::test_anm_trajectory_generation`.
Native Ubuntu and macOS Python 3.11/3.12 logs show LinDelInt raising
`ImportError: CuPy is required for the 'gpu' engine` from its auto-engine path.
The provider issue `uibcdf/lindelint#8` contains the ElastNetMT consumer case.
Suite-policy run `36311638884` passed. Published GH Run Receptor `1.0.0`
inspected these runs; the failed job logs were read directly.

The Python 3.11/3.12 CI environment omits Pytest Receptor, only the 3.13
environment pins `0.6.0`, and `.github/workflows/CI.yaml` invokes plain
`pytest`. Pin one published version across maintained test environments and
select `--receptor=ci` without changing test selection. Then record a passing
exact-commit matrix and inspect it with GH Run Receptor.

## Why

The current matrix proves an integration failure and does not prove preservation
of user unit settings. Its plain pytest route does not demonstrate the suite's
developer-tool contract.

## What was refuted

The suite-policy workflow passed, but it did not exercise the failing trajectory
cells. Declared support-library dependencies alone do not prove the quantity
boundary respects an existing global policy.

## Scope and exclusions

This record owns ElastNetMT's policy adoption and consumer regression. The
LinDelInt auto-engine implementation belongs to `uibcdf/lindelint#8`.

## Acceptance criteria

Preserve a user-selected PyUnitWizard policy on import, verify the provider fix
on the affected trajectory cells, use a published exact Pytest Receptor pin and
`ci` profile in maintained CI, and record independent adoption evidence.

## Consumer modernization checkpoint — 2026-10-08

The modernization branch preserves an active application unit policy and
bootstraps the shared nm/kJ baseline only when absent. It registers real
ArgDigest value callables, translates invalid quantity inputs to owned errors,
and lazily guards Numba/CuPy through DepDigest. Explicit missing engines and
transitive initialization failures remain errors. Fresh-process tests verify
the import boundary; spectral and trajectory tests protect unit invariance.

Trajectory interpolation now exposes `interpolation_engine` with a vectorized
default. This consumer choice avoids the known provider auto fallback failure
without altering the provider algorithm. Explicit selections still reach
LinDelINT unchanged; the automatic provider route remains unqualified and
uibcdf/lindelint#8 stays open. The removal/review condition is recorded in
`devguide/units_and_conventions.md`.

Scientific, add-on and governance CI select `--receptor=ci` with published
pytest-receptor 1.2.1, available on the UIBCDF main channel for Python
3.11–3.14 and recorded in the central build receipts. Numba is explicit test
tooling so the parity test exercises the accelerated implementation. Existing
scientific sibling revision pins and full test collection are preserved.
GNM calibration is independently owned by #21. This record remains active
pending hosted evidence and the remaining ecosystem/provider review.
