import numpy as np
import pytest

from elastnetmt import GaussianNetworkModel
from elastnetmt import pyunitwizard as puw


@pytest.mark.smoke
def test_gnm_initialization():
    """
    Smoke test to verify GNM can be initialized from a PDB structure
    using the new architecture and MolSysMT.
    """
    pdb_id = "pdb_id:1tcd"

    gnm = GaussianNetworkModel(
        pdb_id, selection='atom_name=="CA"', cutoff="7 angstroms"
    )

    assert gnm.n_nodes > 0
    assert gnm.contacts is not None

    # Use puw to check the value in angstroms
    cutoff_angstroms = puw.get_value(gnm.cutoff, to_unit="angstroms")
    assert np.isclose(cutoff_angstroms, 7.0)

    # Assert Lazy Evaluation: spectral data should be None initially
    assert gnm._eigenvalues is None

    # Trigger calculation
    e_vals = gnm.get_eigenvalues()

    # Now spectral data should be present
    assert gnm._eigenvalues is not None
    assert len(e_vals) == gnm.n_nodes

    # Verify first eigenvalue is 0 (within tolerance) for GNM
    assert np.isclose(e_vals[0], 0.0, atol=1e-8)


@pytest.mark.smoke
def test_gnm_parameter_reset():
    """
    Verify that changing parameters resets spectral results (Lazy Evaluation).
    """
    pdb_id = "pdb_id:1tcd"
    gnm = GaussianNetworkModel(pdb_id, cutoff="7 angstroms")

    # Trigger calculation
    gnm.get_eigenvalues()
    assert gnm._eigenvalues is not None

    # Change cutoff - should reset the state
    gnm.calculate_contacts(cutoff="10 angstroms")
    assert gnm._eigenvalues is None

    cutoff_angstroms = puw.get_value(gnm.cutoff, to_unit="angstroms")
    assert np.isclose(cutoff_angstroms, 10.0)
