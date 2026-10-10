"""Rigid nullity and relative tolerance protect actual vibrational modes."""

import numpy as np
import pytest

from elastnetmt import (
    AnisotropicNetworkModel,
    CutoffOptimizationError,
    DegenerateNetworkError,
    GaussianNetworkModel,
    InvalidSpectrumError,
    UndefinedCorrelationError,
)
from elastnetmt._private.spectral import validate_spectrum


@pytest.mark.parametrize("scale", [1e-12, 1, 1e12])
def test_roundoff_is_zero_but_a_resolved_soft_mode_is_retained(scale):
    values = np.array([-1e-16, 1e-12, 2.0]) * scale
    result, vectors = validate_spectrum(
        values, np.eye(3), expected_zero_modes=1, model="GNM"
    )
    assert result[0] == 0
    np.testing.assert_array_equal(result[1:], values[1:])
    np.testing.assert_array_equal(vectors, np.eye(3))
    assert values[0] < 0  # Validation must not mutate the caller's spectrum.


@pytest.mark.parametrize(
    "values", [[-0.01, 1, 2], [0.1, 1, 2], [0, 2, 1], [0, np.nan, 2], [0, 1, np.inf]]
)
def test_invalid_eigenvalues_are_rejected(values):
    with pytest.raises(InvalidSpectrumError) as caught:
        validate_spectrum(values, np.eye(3), expected_zero_modes=1, model="GNM")
    assert caught.value.code == "ENM-E030"


def test_more_than_one_gnm_zero_is_an_explicit_degeneracy():
    with pytest.raises(DegenerateNetworkError) as caught:
        validate_spectrum([0, 0, 2], np.eye(3), expected_zero_modes=1, model="GNM")
    assert caught.value.extra["n_zero_modes"] == 2


@pytest.mark.parametrize("vectors", [np.zeros((3, 2)), np.full((3, 3), np.nan)])
def test_invalid_eigenvectors_are_rejected(vectors):
    with pytest.raises(InvalidSpectrumError):
        validate_spectrum([0, 1, 2], vectors, expected_zero_modes=1, model="GNM")


def test_a_bad_backend_result_never_becomes_a_cached_spectrum(network_pdb, monkeypatch):
    model = GaussianNetworkModel(network_pdb, engine="vectorized")
    import elastnetmt.model.gaussian_network_model as gnm_module

    real_eigh = gnm_module.la.eigh

    def negative(matrix):
        values, vectors = real_eigh(matrix)
        values[0] = -1
        return values, vectors

    monkeypatch.setattr(gnm_module.la, "eigh", negative)
    for _ in range(2):
        with pytest.raises(InvalidSpectrumError):
            model.get_eigenvalues()
        assert model._eigenvalues is None
        assert model.kirchhoff_matrix is None
        assert model.engine_used is None
    monkeypatch.setattr(gnm_module.la, "eigh", real_eigh)
    assert np.all(model.get_eigenvalues()[1:] > 0)


@pytest.mark.parametrize(
    "error",
    [
        DegenerateNetworkError(
            extra={"model": "GNM", "n_zero_modes": 2, "expected_zero_modes": 1}
        ),
        InvalidSpectrumError(extra={"model": "GNM", "reason": "negative eigenvalue"}),
        UndefinedCorrelationError(extra={"argument": "b_factor"}),
        CutoffOptimizationError(),
    ],
)
def test_scientific_exception_reconstruction_preserves_code_and_hint(error):
    rebuilt = type(error)(*error.args)
    assert rebuilt.code == error.code
    assert str(rebuilt) == str(error)


def test_unrepresentable_spectral_inverse_is_rejected_and_rolled_back(
    network_pdb, monkeypatch
):
    model = GaussianNetworkModel(network_pdb, engine="vectorized")
    import elastnetmt.model.gaussian_network_model as gnm_module

    real_eigh = gnm_module.la.eigh

    def tiny(matrix):
        values, vectors = real_eigh(matrix)
        values[0] = 0
        values[1:] *= 1e-310
        return values, vectors

    monkeypatch.setattr(gnm_module.la, "eigh", tiny)
    with pytest.raises(InvalidSpectrumError, match="numerical range"):
        model.get_b_factors()
    assert model._eigenvalues is None
    assert model.kirchhoff_matrix is None
    assert model.b_factors_theo is None


def test_anm_validates_backend_shape_before_reading_diagnostics(
    network_pdb, monkeypatch
):
    model = AnisotropicNetworkModel(network_pdb, engine="vectorized")
    import elastnetmt.model.anisotropic_network_model as anm_module

    monkeypatch.setattr(
        anm_module.la, "eigh", lambda matrix: (np.empty(0), np.empty((0, 0)))
    )
    with pytest.raises(InvalidSpectrumError):
        model.get_eigenvalues()
    assert model._eigenvalues is None
    assert model.hessian_matrix is None
    assert model.engine_used is None
