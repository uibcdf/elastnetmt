import molsysmt as msm
import numpy as np

from elastnetmt import pyunitwizard as puw


def get_contacts(
    molecular_system,
    selection='atom_name=="CA"',
    structure_index=0,
    cutoff="12 angstroms",
    syntax="MolSysMT",
):
    """
    Standardize and calculate the contact map (adjacency matrix).
    """

    atom_indices = msm.select(molecular_system, selection=selection, syntax=syntax)

    # Ensure cutoff is a quantity and standardize it
    if isinstance(cutoff, str):
        cutoff = puw.parse.parse(cutoff)

    cutoff_standardized = puw.standardize(cutoff)

    contacts = msm.structure.get_contacts(
        molecular_system,
        selection=atom_indices,
        structure_indices=structure_index,
        threshold=cutoff_standardized,
    )

    # contacts is a list of arrays (one per frame)
    contacts = contacts[0]

    # Ensure no self-contacts
    np.fill_diagonal(contacts, False)

    return contacts, atom_indices, cutoff_standardized
