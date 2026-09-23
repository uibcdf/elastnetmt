import molsysmt as msm
import numpy as np
import smonitor
from argdigest import arg_digest
from depdigest import dep_digest

from elastnetmt._private.contacts import get_contacts


class ElasticNetworkModel:
    """
    Base class for Elastic Network Models (ENM).
    """

    @arg_digest()
    def __init__(
        self,
        molecular_system,
        selection='atom_name=="CA"',
        structure_index=0,
        cutoff="12 angstroms",
        syntax="MolSysMT",
    ):

        self._input_molecular_system = molecular_system
        self._input_selection = selection
        self._input_structure_index = structure_index
        self._input_syntax = syntax

        self.molecular_system = msm.convert(
            molecular_system,
            to_form="molsysmt.MolSys",
            structure_indices=structure_index,
        )

        self.atom_indices = None
        self.n_nodes = 0
        self.cutoff = None
        self.contacts = None

        self._eigenvalues = None
        self._eigenvectors = None
        self._frequencies = None
        self._modes = None

        self.calculate_contacts(selection=selection, cutoff=cutoff, syntax=syntax)

    @arg_digest()
    def calculate_contacts(self, selection=None, cutoff=None, syntax=None):
        """
        Calculates the contact map and checks for connectivity issues.
        """
        if selection is None:
            selection = self._input_selection
        if cutoff is None:
            cutoff = self.cutoff
        if syntax is None:
            syntax = self._input_syntax

        contacts, atom_indices, cutoff_std = get_contacts(
            self.molecular_system,
            selection=selection,
            structure_index=0,
            cutoff=cutoff,
            syntax=syntax,
        )

        self.contacts = contacts
        self.atom_indices = atom_indices
        self.cutoff = cutoff_std
        self.n_nodes = self.contacts.shape[0]

        # --- SMonitor Instrumentation: Network Metrics ---
        node_degrees = self.contacts.sum(axis=1)
        avg_degree = np.mean(node_degrees)
        std_degree = np.std(node_degrees)
        isolated_nodes = np.where(node_degrees == 0)[0]

        smonitor.emit(
            "DEBUG",
            "elastnetmt.model.selection",
            source="elastnetmt.model.ElasticNetworkModel",
            extra={
                "n_nodes": self.n_nodes,
                "avg_degree": float(avg_degree),
                "std_degree": float(std_degree),
            },
        )

        if len(isolated_nodes) > 0:
            smonitor.emit_from_catalog(
                "ENM-W001",
                cutoff=self.cutoff,
                n_isolated=len(isolated_nodes),
                source="elastnetmt.model.ElasticNetworkModel",
            )

        if avg_degree < 4.0:
            smonitor.emit_from_catalog(
                "ENM-W005",
                avg_degree=float(avg_degree),
                source="elastnetmt.model.ElasticNetworkModel",
            )

        self._reset_spectral_results()

    def _reset_spectral_results(self):
        self._eigenvalues = None
        self._eigenvectors = None
        self._frequencies = None
        self._modes = None

    @dep_digest("matplotlib")
    def show_contact_map(self, cmap="binary"):
        from matplotlib import pyplot as plt

        plt.matshow(self.contacts, cmap=cmap)
        plt.title(f"Contact Map (Cutoff: {self.cutoff})")
        return plt.show()

    @dep_digest("nglview")
    def view(self, protein=True, network=False, representation="cartoon"):
        view = msm.view(self.molecular_system)
        if not protein:
            view.clear()
        if network:
            pass
        return view
