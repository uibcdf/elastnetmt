"""Defined correlations, explicit units and representable scales are required."""

import numpy as np
import pytest

from elastnetmt import ArgumentError
from elastnetmt import pyunitwizard as puw
from elastnetmt._private.b_factors import experimental_profile, fit_profiles


def test_wrong_dimensionality_has_owned_b_factor_error():
    with pytest.raises(ArgumentError, match="b_factor"):
        experimental_profile(puw.quantity([1, 2, 3], "ps"), n_nodes=3)


@pytest.mark.parametrize("profile", [np.arange(8).reshape(2, 4), [1, 2]])
def test_each_node_requires_one_value_in_one_structure(profile):
    with pytest.raises(ArgumentError, match="b_factor"):
        experimental_profile(puw.quantity(profile, "angstroms**2"), n_nodes=8)


def test_large_finite_profiles_have_defined_correlation():
    theoretical = np.array([1.0, 2.0, 4.0])
    experimental = theoretical * 2e200
    before = experimental.copy()
    scale, correlation = fit_profiles(experimental, theoretical)
    np.testing.assert_allclose(scale, 2e200)
    np.testing.assert_allclose(correlation, 1)
    np.testing.assert_array_equal(experimental, before)


def test_unrepresentable_scale_has_owned_error_without_runtime_warning():
    with pytest.raises(ArgumentError, match="representable finite calibration"):
        fit_profiles(np.array([2e307, 4e307, 8e307]), np.array([1e-3, 2e-3, 4e-3]))


def test_finite_scale_with_overflowing_predictions_is_rejected():
    with pytest.raises(ArgumentError, match="finite calibration scale and prediction"):
        fit_profiles(np.array([1.7e308, 1.7e308, 1.6e308]), np.array([1.0, 1.0, 2.0]))
