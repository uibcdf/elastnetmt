# Units and Conventions

Consistency in physical quantities is critical for reproducibility. ElastNetMT strictly uses **PyUnitWizard** for all inputs and outputs.

## Standard Units

When no application policy exists, ElastNetMT initializes the shared MolSysMT
baseline. An existing PyUnitWizard policy, including its provenance, survives
import. Numerical boundaries convert to explicit units independently of that
policy:
- **Distance:** Nanometers (nm)
- **Time:** Picoseconds (ps)
- **Mass:** Dalton
- **Energy:** kJ/mol
- **Angle:** Radians

The complete bootstrap policy is maintained in `elastnetmt/_pyunitwizard.py`.

## Scientific input and spectrum contracts

Selected coordinates must be finite and exactly distinct. GNM requires at
least two nodes; ANM requires at least three. The contact-map base class can
represent a single node. Validation precedes contact calculation so an empty
selection or coincident coordinates do not leak provider errors or divisions
by zero. Near coincidences retain their actual geometry; no hidden physical
distance cutoff is imposed.

The normalized GNM spectrum has one rigid zero mode. The fully constrained
ANM spectrum has six. This matches the nonzero-mode pseudoinverse formulation
in [iGNM 2.0](https://doi.org/10.1093/nar/gkv1236) and the ANM formulation of
[Atilgan et al.](https://doi.org/10.1016/S0006-3495(01)76033-X).
ElastNetMT rejects extra unconstrained modes instead of treating them as
vibrations. Positive semidefiniteness, finite eigenpairs and shape/order are
checked before publishing caches. Numerical zero tolerance is
`32 * float64_epsilon * dimension * spectral_radius`; values inside it are
normalized to zero. Resolved soft modes remain positive. Significant negative
eigenvalues indicate an invalid decomposition; review the matrix construction
and numerical backend.

`DegenerateNetworkError` (`ENM-E020`) and `InvalidSpectrumError` (`ENM-E030`)
subclass `InternalAlgorithmError`. Only successful calculations publish
spectra, matrices and `engine_used`. Successful contact changes invalidate
all dependent matrices and calibration. Assignment-only fit, contact update
and cutoff-search transactions restore prior attribute/array references on
failure or interruption without copying dense matrices per candidate.

## Physical Parameters

### Cutoff Distance
The default cutoff is typically `7 angstroms` for GNM and `12 angstroms` for ANM. Users can provide quantities in any unit (e.g., `0.7 nm`), but they must be standardized before calculation:

```python
from elastnetmt import pyunitwizard as puw
cutoff = puw.standardize(cutoff)
```

### Spectral quantities and B factors

GNM and ANM currently use normalized unit springs. Their eigenvalues and mode
vectors are dimensionless; frequencies derived from them are not physical
frequencies. ANM rejects non-`None` `stiffness` instead of silently ignoring it.

GNM stores the uncalibrated Kirchhoff pseudoinverse diagonal in
`b_factors_theo`. Before fitting, `get_b_factors()` returns that dimensionless
prediction. `fit_to_experimental_b_factors()` reads experimental values in
square angstroms and determines a scalar scale without modifying the raw
prediction. After fitting, `get_b_factors()` returns magnitudes in square
angstroms, applying the scale once. Repeating the fit is stable; recalculating
contacts invalidates the fit. Plotting experimental values fits first when
necessary, and cutoff search refits the selected network before returning.

Fitting/Pearson comparison requires one finite, nonnegative experimental value
per node in a single structure, and varying experimental and theoretical
profiles. Variation at or below `64 * float64_epsilon * profile_maximum` is
numerically constant and raises `UndefinedCorrelationError` (`ENM-E011`).
Missing/invalid experimental data raise `ArgumentError`; raw predictions
remain available without experimental observations. Scaled profiles avoid
overflow in correlation. Unrepresentable spectral inverses, calibration scales
and calibrated predictions are rejected before publishing their results.

Cutoff search fixes the current node indices and experimental snapshot for
the whole grid. It skips only degenerate spectra and constant theoretical
profiles. All other data/backend failures propagate. If no candidate is
admissible, `CutoffOptimizationError` (`ENM-E021`) retains the prior state.

### Trajectory amplitude

ANM interpolates dimensionless mode vectors, normalizes their maximum target
atom norm, and multiplies by the requested amplitude in nanometers once.
`amplitude="2 angstroms"` and `amplitude="0.2 nm"` give the same trajectory.
The sampled maximum displacement reaches the requested amplitude when the
frame grid includes a sine extremum, for example with eight frames.

### Optional engines

Core `auto` selects Numba when discoverable, otherwise NumPy. Explicit
`parallel` and `gpu` require Numba and CuPy respectively; dependency absence
raises instead of silently changing the engine. Backend initialization and
transitive import errors propagate. `engine_used` records the selected core
engine after solving. Importing ElastNetMT itself does not load either backend.

Trajectory interpolation defaults to `vectorized` and exposes
`interpolation_engine` separately. This bounded consumer workaround avoids the
known automatic fallback defect owned by
[uibcdf/lindelint#8](https://github.com/uibcdf/lindelint/issues/8). Explicit
interpolation selections are forwarded unchanged. Reconsider the default
only after the provider's automatic route is qualified on the complete
affected Python/platform matrix; do not duplicate its interpolation algorithm.

## Selection Logic
Selection strings must follow the **MolSysMT** syntax (standard: `MolSysMT`). By default, models are built using `atom_name=="CA"` (alpha-carbons).
