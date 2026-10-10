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

## Integrated consumer checkpoint — 2026-10-10

[PR #22](https://github.com/uibcdf/elastnetmt/pull/22) was merged as
`83293db9c8b06b401778aa937e28dbe1de04c9c4`. Its qualified source f3e6456
passed all eight Linux/macOS arm64 Python 3.11–3.14 test jobs, the viewer
contract, suite policy and publication governance. The PR records the
exact-source workflow evidence. Local calibration and scientific edge-case
reports #21/#23 are resolved and archived. This record stays active for the
remaining ecosystem/provider review; the LinDelINT automatic route and public
installed delivery are not established by the consumer workaround.


## Legacy runtime retirement checkpoint — 2026-10-10

The inactive Python 2 module `elastnetmt/model/old_anm.py` has been moved byte for
byte to `devguide/legacy/old_anm.py.txt`. Its SHA256 is
`89a6503cf59b211f80a7b039efa0e4cabb8d353d5078c40563c180a45d991376`.
The current runtime inventory and Ruff scope no longer include the old module.
`devtools/tests/test_native_wheel.py` compiles all current Python runtime source,
checks complete ownership coverage and rejects a wheel containing the retired
module. Historical noarch files remain unchanged; their temporary test fixture
reconstructs the original source from the archive.

A new ABI3 wheel built from the source archive contains no legacy source or
archive text and passes all 218 installed tests on Linux/Python 3.14. All 42
owned Python/native hashes match before and after science. This closes the
legacy cleanup identified in this review, without closing the remaining
provider/ecosystem and public-delivery work in #14.


## Remove the redundant legacy copy — 2026-10-10

After maintainer review, the repository copy `devguide/legacy/old_anm.py.txt`
is removed. Git history retains the original implementation; the short retirement
note remains in `devguide/legacy/README.md`. Historical distribution tests now
create a synthetic resource placeholder because their contract checks paths and
metadata, not the old algorithm or original source bytes. The current inventory
and negative wheel guard continue to exclude the retired runtime module.
