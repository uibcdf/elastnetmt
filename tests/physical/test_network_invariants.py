"""Small analytic networks verify invariants independent of protein correlations."""

import molsysmt as msm
import numpy as np
import pytest

from elastnetmt import AnisotropicNetworkModel, GaussianNetworkModel
from elastnetmt import pyunitwizard as puw


@pytest.mark.parametrize("engine", ["vectorized", "rust"])
def test_kirchhoff_is_a_symmetric_graph_laplacian(network_pdb, engine):
    model = GaussianNetworkModel(network_pdb, engine=engine)
    eigenvalues = model.get_eigenvalues()
    matrix = model.kirchhoff_matrix
    np.testing.assert_allclose(matrix, matrix.T)
    np.testing.assert_allclose(matrix.sum(axis=1), 0, atol=1e-12)
    np.testing.assert_allclose(eigenvalues[0], 0, atol=1e-12)
    assert np.all(eigenvalues[1:] > 0)
    expected = np.diag(np.linalg.pinv(matrix, hermitian=True))
    np.testing.assert_allclose(model.get_b_factors(), expected, atol=1e-12)


@pytest.mark.parametrize("engine", ["vectorized", "rust"])
def test_hessian_has_six_rigid_modes_and_symmetric_blocks(network_pdb, engine):
    model = AnisotropicNetworkModel(network_pdb, engine=engine)
    values = model.get_eigenvalues(include_rigid_modes=True)
    np.testing.assert_allclose(model.hessian_matrix, model.hessian_matrix.T, atol=1e-12)
    np.testing.assert_allclose(values[:6], 0, atol=1e-12)
    assert np.all(values[6:] > 0)
    for axis in range(3):
        displacement = np.tile(np.eye(3)[axis], model.n_nodes)
        np.testing.assert_allclose(model.hessian_matrix @ displacement, 0, atol=1e-12)


@pytest.mark.parametrize("engine", ["vectorized", "rust"])
def test_anm_spectrum_is_invariant_to_rotation_and_translation(network_pdb, engine):
    original = AnisotropicNetworkModel(network_pdb, engine=engine)
    expected = original.get_eigenvalues()
    system = msm.copy(original.molecular_system)
    coordinates = puw.get_value(msm.get(system, coordinates=True), to_unit="nanometers")
    rotation = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    transformed = coordinates @ rotation + [2, -3, 4]
    msm.set(system, coordinates=puw.quantity(transformed, "nanometers"))
    model = AnisotropicNetworkModel(system, engine=engine)
    np.testing.assert_allclose(model.get_eigenvalues(), expected, atol=1e-12)


@pytest.mark.parametrize("engine", ["vectorized", "rust"])
def test_gnm_predictions_are_invariant_to_application_units(network_pdb, engine):
    values = []
    for units in (["nm", "ps", "kJ/mol"], ["angstroms", "ns", "kcal/mol"]):
        with puw.context(standard_units=units):
            model = GaussianNetworkModel(network_pdb, engine=engine)
            model.fit_to_experimental_b_factors()
            values.append(model.get_b_factors())
    np.testing.assert_allclose(*values)
