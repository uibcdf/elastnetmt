from contextlib import contextmanager

import molsysmt as msm
import numpy as np
import smonitor
from argdigest import arg_digest
from depdigest import dep_digest

from elastnetmt._private.arguments import invalid
from elastnetmt._private.contacts import get_contacts
from elastnetmt._private.smonitor import emit_catalog


class ElasticNetworkModel:
    """Represent selected molecular nodes and their cutoff contact map.

    The base class builds contacts; use GaussianNetworkModel or
    AnisotropicNetworkModel for spectral calculations.

    Attributes
    ----------
    molecular_system : molsysmt.MolSys
        Converted molecular system containing the chosen input structure.
    atom_indices : numpy.ndarray
        Node indices in the converted system, in contact-matrix order.
    n_nodes : int
        Number of selected nodes.
    contacts : numpy.ndarray
        Shape ``(n_nodes, n_nodes)``. Symmetric adjacency matrix with a false diagonal.
    cutoff : quantity
        Contact threshold standardized with PyUnitWizard.

    Examples
    --------
    Use the PDB bundled with MolSysMT without downloading a structure.

    >>> from importlib.resources import as_file, files
    >>> from elastnetmt import ElasticNetworkModel
    >>> resource = files('molsysmt').joinpath('data/pdb/1tcd.pdb')
    >>> with as_file(resource) as path:
    ...     network = ElasticNetworkModel(str(path))
    >>> assert network.contacts.shape == (network.n_nodes, network.n_nodes)
    >>> assert not network.contacts.diagonal().any()
    """

    _minimum_nodes = 1

    @contextmanager
    def _restore_state_on_failure(self):
        """Restore attribute references if an assignment-only calculation fails.

        Consumers must allocate new arrays rather than mutate borrowed cached
        arrays in place. This preserves existing caches without copying dense
        matrices for each candidate cutoff, including on interruption.
        """
        previous = self.__dict__.copy()
        try:
            yield
        except BaseException:
            self.__dict__.clear()
            self.__dict__.update(previous)
            raise

    @arg_digest()
    def __init__(
        self,
        molecular_system,
        selection='atom_name=="CA"',
        structure_index=0,
        cutoff="12 angstroms",
        syntax="MolSysMT",
    ):
        """Initialize a contact network from one molecular structure.

        Parameters
        ----------
        molecular_system : object
            Molecular system in a form accepted by MolSysMT, such as a PDB path.
        selection : str, default='atom_name=="CA"'
            MolSysMT selection expression defining the network nodes.
        structure_index : int, default=0
            Zero-based input structure index; must be nonnegative.
        cutoff : str or quantity, default='12 angstroms'
            Finite positive scalar distance with explicit length units.
        syntax : str, default='MolSysMT'
            Selection language interpreted by MolSysMT.

        Raises
        ------
        elastnetmt.ArgumentError
            If the cutoff or node coordinates are invalid, nodes coincide,
            or the selection has fewer nodes than the model requires.

        Notes
        -----
        The base class permits one node; GNM requires two and ANM three.
        Construction validates coordinates and builds contacts. Subclasses
        validate connectivity and geometric constraints when solving.
        """

        self._input_molecular_system = molecular_system
        self._input_selection = selection
        self._input_structure_index = structure_index
        self._input_syntax = syntax
        if cutoff is None:
            invalid("cutoff", "a positive scalar length for a new network")

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
        """Rebuild contacts and invalidate dependent spectra and calibration.

        Parameters
        ----------
        selection : str or None, default=None
            Node expression. None reuses the original constructor selection.
        cutoff : str, quantity or None, default=None
            Positive scalar length. None retains the current cutoff.
        syntax : str or None, default=None
            Selection language. None reuses the constructor syntax.

        Returns
        -------
        None
            Update contacts, node indices and cutoff in place.

        Raises
        ------
        elastnetmt.ArgumentError
            If the selection, coordinates or cutoff violate the input contract.

        Notes
        -----
        A failed update preserves the previous state. Diagnostics for isolated
        or low-degree nodes do not establish connectedness; spectral queries
        enforce the subclass's null-mode contract.
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
            minimum_nodes=self._minimum_nodes,
        )

        with self._restore_state_on_failure():
            self._set_contacts(contacts, atom_indices, cutoff_std)

    def _set_contacts(self, contacts, atom_indices, cutoff):
        """Adopt validated contacts and invalidate every dependent calculation."""

        self.contacts = contacts
        self.atom_indices = atom_indices
        self.cutoff = cutoff
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
            emit_catalog(
                "ENM-W001",
                cutoff=self.cutoff,
                n_isolated=len(isolated_nodes),
                source="elastnetmt.model.ElasticNetworkModel",
            )

        if avg_degree < 4.0:
            emit_catalog(
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
        self.engine_used = None

    @dep_digest("matplotlib")
    def show_contact_map(self, cmap="binary"):
        """Display the current adjacency matrix with Matplotlib.

        Parameters
        ----------
        cmap : str or matplotlib.colors.Colormap, default='binary'
            Colormap passed to Matplotlib.

        Returns
        -------
        None
            Display the figure using the active Matplotlib backend.

        Raises
        ------
        ImportError
            If the plotting dependency is unavailable or cannot initialize.
        """
        from matplotlib import pyplot as plt

        plt.matshow(self.contacts, cmap=cmap)
        plt.title(f"Contact Map (Cutoff: {self.cutoff})")
        return plt.show()

    @dep_digest("nglview")
    def view(self, protein=True, network=False, representation="cartoon"):
        """Create a molecular viewer through MolSysMT.

        Parameters
        ----------
        protein : bool, default=True
            Retain the initial representation. False calls the viewer's clear
            operation and requires that the returned viewer support it.
        network : bool, default=False
            Reserved flag; contact-network rendering is currently unimplemented.
        representation : str, default='cartoon'
            Reserved argument; the delegated viewer's default is currently used.

        Returns
        -------
        object
            Viewer returned by MolSysMT; its type depends on the provider.

        Raises
        ------
        ImportError
            If NGLView or the provider's selected viewer is unavailable.

        Notes
        -----
        Interactive display requires a compatible notebook frontend. For
        ENM overlays, see the separate MolSysViewer add-on.
        """
        view = msm.view(self.molecular_system)
        if not protein:
            view.clear()
        if network:
            pass
        return view
