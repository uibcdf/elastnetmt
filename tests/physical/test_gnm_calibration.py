"""Regression evidence for the physical GNM B-factor calibration contract (#21)."""

import matplotlib.pyplot as plt
import numpy as np
import pytest

from elastnetmt import GaussianNetworkModel
from elastnetmt import pyunitwizard as puw


def model(path):
    return GaussianNetworkModel(path, cutoff="7 angstroms", engine="vectorized")


def test_repeated_fit_preserves_scale_and_predictions(network_pdb):
    gnm = model(network_pdb)
    first_scale, first_corr = gnm.fit_to_experimental_b_factors()
    first_prediction = gnm.get_b_factors().copy()
    second_scale, second_corr = gnm.fit_to_experimental_b_factors()
    np.testing.assert_allclose(second_scale, first_scale)
    np.testing.assert_allclose(second_corr, first_corr)
    np.testing.assert_allclose(gnm.get_b_factors(), first_prediction)


@pytest.mark.parametrize("pre_fit", [False, True])
def test_plot_matches_fitted_predictions(network_pdb, monkeypatch, pre_fit):
    gnm = model(network_pdb)
    if pre_fit:
        gnm.fit_to_experimental_b_factors()
    monkeypatch.setattr(plt, "show", lambda: None)
    try:
        gnm.show_b_factors()
        theoretical = plt.gca().lines[0].get_ydata()
        np.testing.assert_allclose(theoretical, gnm.get_b_factors())
        np.testing.assert_allclose(plt.gca().lines[1].get_ydata(), gnm.b_factors_exp)
    finally:
        plt.close("all")


def test_best_cutoff_refits_the_selected_network(network_pdb):
    gnm = model(network_pdb)
    cutoff, correlation = gnm.get_best_cutoff("6 angstroms", "10 angstroms", 3)
    expected = GaussianNetworkModel(network_pdb, cutoff=cutoff, engine="vectorized")
    expected_scale, expected_corr = expected.fit_to_experimental_b_factors()
    np.testing.assert_allclose(gnm.scaling_factor, expected_scale)
    np.testing.assert_allclose(correlation, expected_corr)
    np.testing.assert_allclose(gnm.get_b_factors(), expected.get_b_factors())


def test_experimental_b_factors_are_fixed_square_angstrom_values(network_pdb):
    with puw.context(standard_units=["angstroms", "ps", "kJ/mol"]):
        reference = model(network_pdb)
        reference.fit_to_experimental_b_factors()
        expected = reference.get_b_factors()
    with puw.context(standard_units=["nm", "ns", "kcal/mol"]):
        other = model(network_pdb)
        other.fit_to_experimental_b_factors()
        np.testing.assert_allclose(other.b_factors_exp, np.arange(1, 9) * 10)
        np.testing.assert_allclose(other.get_b_factors(), expected)
