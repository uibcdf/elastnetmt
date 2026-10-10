"""Public argument constraints execute through the real ArgDigest registry."""

import pytest

from elastnetmt import AnisotropicNetworkModel, ArgumentError, GaussianNetworkModel


@pytest.mark.parametrize("model", [GaussianNetworkModel, AnisotropicNetworkModel])
@pytest.mark.parametrize("engine", ["invalid-engine", None, True])
def test_invalid_engine_is_rejected_before_loading_a_system(model, engine):
    with pytest.raises(ArgumentError, match="engine"):
        model("missing.pdb", engine=engine)


@pytest.mark.parametrize("cutoff", [7, "3 ps", "-1 nm", "0 nm"])
def test_invalid_cutoff_has_an_owned_argument_error(cutoff):
    with pytest.raises(ArgumentError, match="cutoff"):
        GaussianNetworkModel("missing.pdb", cutoff=cutoff)


@pytest.mark.parametrize("n_modes", [0, -1, True, "invalid"])
def test_invalid_mode_counts_are_rejected(network_pdb, n_modes):
    gnm = GaussianNetworkModel(network_pdb, engine="vectorized")
    with pytest.raises(ArgumentError, match="n_modes"):
        gnm.get_b_factors(n_modes=n_modes)


def test_unimplemented_stiffness_is_not_silently_ignored():
    with pytest.raises(ArgumentError, match="stiffness"):
        AnisotropicNetworkModel("missing.pdb", stiffness="1 kcal/(mol*nm**2)")


def test_argument_exception_reconstructs_without_duplicating_its_hint():
    with pytest.raises(ArgumentError) as caught:
        GaussianNetworkModel("missing.pdb", engine="typo")
    original = caught.value
    reconstructed = type(original)(*original.args)
    assert str(reconstructed) == str(original)


def test_out_of_range_trajectory_mode_has_owned_error(network_pdb):
    anm = AnisotropicNetworkModel(network_pdb, engine="vectorized")
    with pytest.raises(ArgumentError, match="mode"):
        anm.trajectory_along_mode(mode=3 * anm.n_nodes)


@pytest.mark.parametrize("bounds", [("0 nm", "1 nm"), ("2 nm", "1 nm")])
def test_invalid_cutoff_search_bounds(network_pdb, bounds):
    gnm = GaussianNetworkModel(network_pdb, engine="vectorized")
    with pytest.raises(ArgumentError, match="min_cutoff/max_cutoff"):
        gnm.get_best_cutoff(*bounds)
