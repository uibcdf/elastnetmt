import numpy as np
import pytest

from elastnetmt import GaussianNetworkModel
from elastnetmt import pyunitwizard as puw


@pytest.mark.physical
def test_gnm_bfactors_correlation():
    """
    Physical validation: GNM B-factors should correlate well with
    experimental values for T4 Lysozyme (1TCD).
    """
    pdb_id = "pdb_id:1tcd"

    # 1. Initialize GNM with a standard cutoff
    gnm = GaussianNetworkModel(
        pdb_id, selection='atom_name=="CA"', cutoff="8 angstroms"
    )

    # 2. Fit to experimental data
    scaling, correlation = gnm.fit_to_experimental_b_factors()

    # 3. Assertions
    # Typical GNM correlation for proteins is > 0.6
    assert correlation > 0.5
    assert scaling > 0.0

    # Verify theoretical factors are populated
    theo_b = gnm.get_b_factors()
    assert len(theo_b) == gnm.n_nodes
    assert not np.any(np.isnan(theo_b))


@pytest.mark.physical
def test_gnm_best_cutoff_optimization():
    """
    Verify that the cutoff optimization improves correlation.
    """
    pdb_id = "pdb_id:1tcd"
    gnm = GaussianNetworkModel(pdb_id, selection='atom_name=="CA"')

    # Initial fit with default (7A)
    _, initial_corr = gnm.fit_to_experimental_b_factors()

    # Optimize
    best_cutoff, best_corr = gnm.get_best_cutoff(
        min_cutoff="6 A", max_cutoff="12 A", steps=5
    )

    # Assert improvement or at least equality
    assert best_corr >= initial_corr
    assert best_cutoff.magnitude > 0


@pytest.mark.physical
def test_gnm_best_cutoff_accepts_length_variants():
    """
    The cutoff optimizer should accept abbreviated strings and typed quantities.
    """
    pdb_id = "pdb_id:1tcd"

    variants = [
        ("6 A", "12 A"),
        ("6 angstroms", "12 angstroms"),
        (puw.quantity(6.0, "angstroms"), puw.quantity(12.0, "angstroms")),
    ]

    results = []
    for min_cutoff, max_cutoff in variants:
        gnm = GaussianNetworkModel(pdb_id, selection='atom_name=="CA"')
        best_cutoff, best_corr = gnm.get_best_cutoff(
            min_cutoff=min_cutoff,
            max_cutoff=max_cutoff,
            steps=4,
        )
        results.append((best_cutoff, best_corr))

    reference_cutoff = puw.get_value(results[0][0], to_unit="angstroms")
    reference_corr = results[0][1]

    for best_cutoff, best_corr in results[1:]:
        assert np.isclose(
            puw.get_value(best_cutoff, to_unit="angstroms"), reference_cutoff
        )
        assert np.isclose(best_corr, reference_corr)
