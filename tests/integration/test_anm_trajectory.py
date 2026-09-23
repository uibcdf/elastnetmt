import molsysmt as msm
import numpy as np
import pytest

from elastnetmt import AnisotropicNetworkModel


@pytest.mark.integration
def test_anm_trajectory_generation():
    """
    Verify that ANM can generate a full-atom trajectory using lindelint
    and return a valid MolSysMT object.
    """
    pdb_id = "pdb_id:1tcd"  # T4 Lysozyme

    # 1. Initialize ANM (only CA nodes)
    anm = AnisotropicNetworkModel(
        pdb_id, selection='atom_name=="CA"', cutoff="12 angstroms"
    )

    # 2. Generate trajectory for ALL atoms along the first non-rigid mode (mode 0)
    n_steps = 20
    traj = anm.trajectory_along_mode(mode=0, selection="all", oscillation_steps=n_steps)

    # 3. Assertions
    assert msm.get_form(traj) == "molsysmt.MolSys"
    n_atoms_original = msm.get(
        anm.molecular_system, element="atom", selection="all", n_atoms=True
    )
    n_atoms_traj = msm.get(traj, element="atom", selection="all", n_atoms=True)

    assert n_atoms_traj == n_atoms_original
    assert msm.get(traj, element="system", n_structures=True) == n_steps

    # Verify that coordinates actually change (it's not a static system)
    coords = msm.get(
        traj, element="atom", selection='atom_name=="CA"', coordinates=True
    )
    assert not np.allclose(coords[0], coords[int(n_steps / 4)])
