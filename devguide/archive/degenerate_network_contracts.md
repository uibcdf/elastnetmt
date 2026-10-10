---
summary: Reject degenerate ENM calculations without publishing partial model state.
issue: uibcdf/elastnetmt#23
status: resolved
opened: 2026-10-09
closed: 2026-10-10
severity: high
verification: measured
area: [physics, validation]
guard: tests/physical/test_degenerate_networks.py
normative:
blocked_by: []
supersedes: []
---

# Degenerate network and calibration contracts

## What

At source 6a3598a, a disconnected GNM returns infinite B factors after an
ERROR diagnostic, an ANM with two nodes raises IndexError, and an empty
selection reaches a provider concatenation ValueError. Underconstrained ANM
spectra expose additional zero modes as vibrations. Constant experimental
profiles return NaN correlation, and cutoff search subsequently parses
"None angstroms". Missing B factors reach PyUnitWizard's unsupported-form
error for None. Failed cutoff calculations also overwrite valid model state.

## How

Validate finite distinct coordinates and model-specific node counts in the
contact owner. Validate finite positive-semidefinite eigenpairs and rigid
nullity through the shared spectral owner before publishing caches. Normalize
only relative roundoff; preserve resolved soft modes. Validate square-length
experimental profiles and fit scaled profiles through the B-factor owner.

Store calculation attributes only after successful validation, and roll back
assignment-only fit/contact/search operations on failure or interruption.
Cutoff search retains current node indices and a fixed experimental snapshot,
skips degenerate spectra and constant theoretical profiles, then refits its
winner. Genuine backend/data failures propagate. Expose owned exception types
and codes so callers can revise their inputs without parsing provider errors.

## Why

These failures produce unusable numerical results, misleading errors and
stale or partial state even when earlier model calculations were valid.

## What is measured and what is assumed

The initial public regression module produced 21 failures and one pass against
6a3598a on Python 3.14.7 with real MolSysMT/NumPy. The calibration, invariant,
trajectory and edge-case selection passed 33 checks after the first correction;
the expanded spectrum, provider absence and TcTIM selection passed 49 checks.
Final complete-suite and hosted evidence are tracked in
[implementation PR #22](https://github.com/uibcdf/elastnetmt/pull/22).
Source checks do not establish public installed delivery or GPU execution.

## Alternatives and refuted paths

Applying abs to significant negative eigenvalues hides invalid decomposition.
Dropping all zero modes changes the current connected/fully constrained ENM
contract and would silently change supported vibrations. Assigning zero
correlation to a constant profile invents a score. A nullable correlation
would change the current fitting return contract. Raw GNM predictions remain
available without an experimental profile.

Copying dense caches at every cutoff is unnecessary: owner calculations
allocate new arrays and assignment rollback preserves existing references.
Catching every exception as a bad cutoff would swallow provider and backend
failures; only the two explicit candidate conditions are skipped.

## Scope and exclusions

Local scientific input, spectrum, fitting and state contracts. The earlier
calibration bug remains #21, provider auto fallback remains lindelint#8,
and installed delivery remains #18/#19. This does not add a physical spring
calibration, iterative solver, successful CUDA qualification or new scientific
attribution boundary. Complete public docstrings and notebooks remain #8/#13.

## Acceptance criteria

The guard rejects empty/coincident/nonfinite nodes, invalid small or
underconstrained ANM, disconnected GNM and undefined B-factor fits. It verifies
failed calculations preserve valid state, recalculation recovers, candidate
search preserves node selection and skips only known candidate failures.
tests/physical/test_spectral_contract.py separately guards relative tolerance,
resolved soft modes, invalid backend spectra and exception reconstruction.
tests/physical/test_b_factor_contract.py guards shape, units and numerical
range, including unrepresentable spectral inverses and calibrated predictions.
Full source matrix and viewer qualification are tracked in PR #22; integration
and report archival remain pending.

## Resolution — 2026-10-10

PR #22 was merged into main as
`83293db9c8b06b401778aa937e28dbe1de04c9c4`, with a tree identical to the
qualified source `f3e64566201ca058acb4bae8ae8b87ab97e42cb7`.
The earlier statements about pending integration and archival are historical
and are superseded by this dated resolution.

The complete local suite passed 127 tests on Python 3.14.7. The targeted
spectrum/profile guards also passed with RuntimeWarning treated as an error.
[Scientific CI run 38030019801](https://github.com/uibcdf/elastnetmt/actions/runs/38030019801)
passed all eight Linux/macOS arm64 Python 3.11–3.14 test jobs and their actual
Run tests steps. PR #22 records the successful exact-source viewer, policy
and publication-governance runs. The durable guards are
`tests/physical/test_degenerate_networks.py`,
`tests/physical/test_spectral_contract.py` and
`tests/physical/test_b_factor_contract.py`.
This resolves the local scientific failure/state contract; provider fallback,
public delivery, full documentation and performance work retain their owners.
