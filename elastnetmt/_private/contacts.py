import molsysmt as msm
import numpy as np

from elastnetmt import pyunitwizard as puw
from elastnetmt._private.arguments import invalid


def validate_node_coordinates(coordinates, *, minimum_nodes=1):
    """Require distinct finite nodes of shape (N, 3) in explicit numeric units.

    Exact coincident nodes are invalid. Near coincidences retain their actual
    geometry; this operation does not impose a hidden physical distance cutoff.
    """
    values = np.asarray(coordinates, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3 or not np.all(np.isfinite(values)):
        invalid("coordinates", "finite node coordinates of shape (N, 3)")
    if len(values) < minimum_nodes:
        invalid("selection", f"at least {minimum_nodes} network nodes")
    if len(np.unique(values, axis=0)) != len(values):
        invalid("coordinates", "distinct node positions without coincident nodes")
    return values


def get_contacts(
    molecular_system,
    selection='atom_name=="CA"',
    structure_index=0,
    cutoff="12 angstroms",
    syntax="MolSysMT",
    minimum_nodes=1,
):
    """
    Standardize and calculate the contact map (adjacency matrix).
    """

    atom_indices = msm.select(molecular_system, selection=selection, syntax=syntax)
    if len(atom_indices) < minimum_nodes:
        invalid("selection", f"at least {minimum_nodes} network nodes")
    coordinates = msm.get(
        molecular_system,
        element="atom",
        selection=atom_indices,
        structure_indices=structure_index,
        coordinates=True,
    )
    validate_node_coordinates(
        puw.get_value(coordinates[0], to_unit="nanometers"),
        minimum_nodes=minimum_nodes,
    )

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
