"""Shared numerical contract for the normalized GNM/ANM eigendecomposition.

Eigenvalues must be finite, sorted and positive semidefinite. Exactly the
expected rigid nullity is admitted. Numerical zeros use a relative tolerance
of 32 * float64 epsilon * matrix dimension * spectral radius; only roundoff
inside that tolerance is normalized to zero. The input arrays are not mutated.
"""

import numpy as np

from .smonitor import DegenerateNetworkError, InvalidSpectrumError


def validate_spectrum(eigenvalues, eigenvectors, *, expected_zero_modes, model):
    """Return finite eigenpairs, rejecting extra zero modes or invalid results."""
    values = np.asarray(eigenvalues, dtype=float)
    vectors = np.asarray(eigenvectors, dtype=float)

    def invalid(reason):
        raise InvalidSpectrumError(extra={"model": model, "reason": reason})

    if values.ndim != 1 or values.size <= expected_zero_modes:
        invalid("the spectrum has no vibrational degrees of freedom")
    if vectors.shape != (values.size, values.size):
        invalid("the eigenvector shape does not match the spectrum")
    if not np.all(np.isfinite(values)) or not np.all(np.isfinite(vectors)):
        invalid("the eigenpairs contain nonfinite values")
    tolerance = 32 * np.finfo(float).eps * values.size * np.max(np.abs(values))
    if np.any(values < -tolerance):
        invalid(
            f"negative eigenvalue {values.min():.3e} exceeds tolerance {tolerance:.3e}"
        )
    if np.any(np.diff(values) < 0):
        invalid("the eigenvalues are not sorted")
    zeros = np.abs(values) <= tolerance
    n_zeros = int(zeros.sum())
    if n_zeros > expected_zero_modes:
        raise DegenerateNetworkError(
            extra={
                "model": model,
                "n_zero_modes": n_zeros,
                "expected_zero_modes": expected_zero_modes,
                "tolerance": float(tolerance),
            }
        )
    if n_zeros < expected_zero_modes:
        invalid(f"found {n_zeros} rigid zero modes, expected {expected_zero_modes}")
    values = values.copy()
    values[zeros] = 0
    return values, vectors
