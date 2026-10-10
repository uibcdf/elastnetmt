"""The interpolated eigenvector is dimensionless; amplitude is a length."""

import molsysmt as msm
import numpy as np

from elastnetmt import AnisotropicNetworkModel
from elastnetmt import pyunitwizard as puw


def test_trajectory_amplitude_and_equivalent_units(network_pdb, monkeypatch):
    import lindelint

    original = lindelint.Interpolator
    engines = []

    def record_engine(*args, **kwargs):
        engines.append(kwargs["engine"])
        return original(*args, **kwargs)

    monkeypatch.setattr(lindelint, "Interpolator", record_engine)
    anm = AnisotropicNetworkModel(network_pdb, engine="vectorized")
    with puw.context(standard_units=["angstroms", "ps", "kJ/mol"]):
        first = anm.trajectory_along_mode(amplitude="2 angstroms", oscillation_steps=8)
    with puw.context(standard_units=["nm", "ns", "kcal/mol"]):
        second = anm.trajectory_along_mode(amplitude="0.2 nm", oscillation_steps=8)
    first_coords = puw.get_value(msm.get(first, coordinates=True), to_unit="nm")
    second_coords = puw.get_value(msm.get(second, coordinates=True), to_unit="nm")
    np.testing.assert_allclose(first_coords, second_coords, atol=1e-12)
    displacement = first_coords[2] - first_coords[0]
    np.testing.assert_allclose(np.linalg.norm(displacement, axis=1).max(), 0.2)
    assert engines == ["vectorized", "vectorized"]
