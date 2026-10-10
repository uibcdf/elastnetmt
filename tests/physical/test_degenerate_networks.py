"""Invalid scientific inputs must fail without publishing partial ENM results."""

import molsysmt as msm
import numpy as np
import pytest

from elastnetmt import (
    AnisotropicNetworkModel,
    ArgumentError,
    GaussianNetworkModel,
    InternalAlgorithmError,
)
from elastnetmt import (
    pyunitwizard as puw,
)


def system(path):
    return msm.convert(path, to_form="molsysmt.MolSys")


@pytest.mark.parametrize("model", [GaussianNetworkModel, AnisotropicNetworkModel])
def test_empty_node_selection_has_an_owned_error(network_pdb, model):
    with pytest.raises(ArgumentError, match="selection"):
        model(network_pdb, selection='atom_name=="NOATOM"', engine="vectorized")


@pytest.mark.parametrize(
    "model,count", [(GaussianNetworkModel, 1), (AnisotropicNetworkModel, 2)]
)
def test_too_few_nodes_has_an_owned_error(network_pdb, model, count):
    with pytest.raises(ArgumentError, match="selection"):
        model(network_pdb, selection=f"atom_index < {count}", engine="vectorized")


@pytest.mark.parametrize("model", [GaussianNetworkModel, AnisotropicNetworkModel])
@pytest.mark.parametrize("problem", ["duplicate", "nan", "inf"])
def test_invalid_node_coordinates_are_rejected(network_pdb, model, problem):
    native = system(network_pdb)
    coords = puw.get_value(msm.get(native, coordinates=True), to_unit="nm").copy()
    if problem == "duplicate":
        coords[0, 1] = coords[0, 0]
    else:
        coords[0, 0, 0] = float(problem)
    msm.set(native, coordinates=puw.quantity(coords, "nm"))
    with pytest.raises(ArgumentError, match="coordinates"):
        model(native, engine="vectorized")


def test_disconnected_components_are_rejected_even_without_isolated_nodes(network_pdb):
    native = system(network_pdb)
    coords = puw.get_value(msm.get(native, coordinates=True), to_unit="nm").copy()
    coords[0, 4:] = coords[0, :4] + [10, 0, 0]
    msm.set(native, coordinates=puw.quantity(coords, "nm"))
    model = GaussianNetworkModel(native, cutoff="12 A", engine="vectorized")
    assert np.all(model.contacts.sum(axis=1) == 3)
    with pytest.raises(InternalAlgorithmError) as caught:
        model.get_b_factors()
    assert caught.value.code == "ENM-E020"
    assert model._eigenvalues is None
    assert model.b_factors_theo is None
    # A failed solve must fail again instead of using its rejected cached spectrum.
    with pytest.raises(InternalAlgorithmError):
        model.get_eigenvalues()
    model.calculate_contacts(cutoff="120 A")
    assert np.all(np.isfinite(model.get_b_factors()))


def test_connected_underconstrained_anm_does_not_publish_spurious_modes(network_pdb):
    connected = GaussianNetworkModel(network_pdb, cutoff="5 A", engine="vectorized")
    assert np.all(connected.get_eigenvalues()[1:] > 0)
    model = AnisotropicNetworkModel(network_pdb, cutoff="5 A", engine="vectorized")
    with pytest.raises(InternalAlgorithmError) as caught:
        model.get_modes()
    assert caught.value.code == "ENM-E020"
    assert model._eigenvalues is None
    assert model._modes is None
    model.calculate_contacts(cutoff="12 A")
    assert np.all(model.get_eigenvalues() > 0)


@pytest.mark.parametrize(
    "profile",
    [None, [0] * 8, [10] * 8, [np.nan] * 8, [np.inf] * 8, [-1, 2, 3, 4, 5, 6, 7, 8]],
)
def test_invalid_experimental_profile_does_not_overwrite_a_valid_fit(
    network_pdb, profile
):
    model = GaussianNetworkModel(network_pdb, engine="vectorized")
    scale, correlation = model.fit_to_experimental_b_factors()
    expected = model.get_b_factors().copy()
    experimental = model.b_factors_exp.copy()
    model.molecular_system.structures.b_factor = (
        None if profile is None else puw.quantity([profile], "angstroms**2")
    )
    with pytest.raises(ArgumentError, match="b_factor"):
        model.fit_to_experimental_b_factors()
    assert model.scaling_factor == scale
    assert np.isfinite(correlation)
    np.testing.assert_allclose(model.b_factors_exp, experimental)
    np.testing.assert_allclose(model.get_b_factors(), expected)


def test_constant_theoretical_profile_cannot_have_a_pearson_correlation(network_pdb):
    model = GaussianNetworkModel(network_pdb, cutoff="12 A", engine="vectorized")
    with pytest.raises(ArgumentError, match="theoretical_b_factors"):
        model.fit_to_experimental_b_factors()
    assert model.b_factors_exp is None
    assert model.scaling_factor == 1


def test_cutoff_search_skips_disconnected_candidates(network_pdb):
    model = GaussianNetworkModel(network_pdb, engine="vectorized")
    cutoff, correlation = model.get_best_cutoff("1 A", "7 A", 3)
    assert puw.get_value(cutoff, to_unit="angstroms") >= 4
    assert np.isfinite(correlation)
    assert np.all(np.isfinite(model.get_b_factors()))


def test_unsuccessful_cutoff_search_preserves_the_previous_state(network_pdb):
    model = GaussianNetworkModel(network_pdb, engine="vectorized")
    model.fit_to_experimental_b_factors()
    before = model.__dict__.copy()
    with pytest.raises(InternalAlgorithmError) as caught:
        model.get_best_cutoff("1 A", "2 A", 3)
    assert caught.value.code == "ENM-E021"
    assert model.__dict__.keys() == before.keys()
    for name, value in before.items():
        assert model.__dict__[name] is value, name


@pytest.mark.parametrize("failure", [ImportError, KeyboardInterrupt])
def test_cutoff_search_does_not_swallow_backend_failures(
    network_pdb, monkeypatch, failure
):
    model = GaussianNetworkModel(network_pdb, engine="vectorized")
    model.fit_to_experimental_b_factors()
    before = model.__dict__.copy()

    def broken(_):
        raise failure("broken native dependency")

    monkeypatch.setattr("elastnetmt.model.gaussian_network_model.la.eigh", broken)
    with pytest.raises(failure, match="broken native dependency"):
        model.get_best_cutoff("6 A", "8 A", 3)
    for name, value in before.items():
        assert model.__dict__[name] is value, name


def test_cutoff_search_preserves_a_selection_changed_after_construction(network_pdb):
    model = GaussianNetworkModel(network_pdb, engine="vectorized")
    model.calculate_contacts(selection="atom_index < 7")
    indices = model.atom_indices.copy()
    cutoff, _ = model.get_best_cutoff("4 A", "7 A", 4)
    np.testing.assert_array_equal(model.atom_indices, indices)
    expected = GaussianNetworkModel(
        network_pdb, selection="atom_index < 7", cutoff=cutoff, engine="vectorized"
    )
    expected.fit_to_experimental_b_factors()
    np.testing.assert_allclose(model.get_b_factors(), expected.get_b_factors())


def test_valid_noncollinear_three_node_anm_is_supported(network_pdb):
    model = AnisotropicNetworkModel(
        network_pdb, selection="atom_index < 3", engine="vectorized"
    )
    values = model.get_eigenvalues(include_rigid_modes=True)
    np.testing.assert_array_equal(values[:6], 0)
    assert np.all(values[6:] > 0)


def test_collinear_anm_is_rejected_without_division_warnings(network_pdb):
    native = system(network_pdb)
    coords = np.zeros((1, 8, 3))
    coords[0, :, 0] = np.arange(8) / 10
    msm.set(native, coordinates=puw.quantity(coords, "nm"))
    model = AnisotropicNetworkModel(native, engine="vectorized")
    with pytest.raises(InternalAlgorithmError) as caught:
        model.get_modes()
    assert caught.value.code == "ENM-E020"


def test_invalid_contact_selection_preserves_a_fitted_model(network_pdb):
    model = GaussianNetworkModel(network_pdb, engine="vectorized")
    model.fit_to_experimental_b_factors()
    before = model.__dict__.copy()
    with pytest.raises(ArgumentError):
        model.calculate_contacts(selection='atom_name=="NOATOM"')
    for name, value in before.items():
        assert model.__dict__[name] is value, name


def test_constant_theoretical_candidates_are_skipped(network_pdb):
    model = GaussianNetworkModel(network_pdb, engine="vectorized")
    cutoff, correlation = model.get_best_cutoff("6 A", "12 A", 4)
    assert puw.get_value(cutoff, to_unit="angstroms") < 10
    assert np.isfinite(correlation)


def test_unavailable_b_factors_do_not_prevent_unfitted_predictions(network_pdb):
    model = GaussianNetworkModel(network_pdb, engine="vectorized")
    model.molecular_system.structures.b_factor = None
    assert np.all(np.isfinite(model.get_b_factors()))


def test_successful_contact_change_invalidates_anm_matrix_and_engine(network_pdb):
    model = AnisotropicNetworkModel(network_pdb, engine="vectorized")
    model.get_modes()
    model.calculate_contacts(cutoff="11 A")
    assert model.hessian_matrix is None
    assert model._modes is None
    assert model.engine_used is None


@pytest.mark.parametrize("model", [GaussianNetworkModel, AnisotropicNetworkModel])
def test_constructor_requires_a_cutoff_before_loading_the_system(model):
    with pytest.raises(ArgumentError, match="cutoff"):
        model("missing.pdb", cutoff=None)
