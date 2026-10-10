import time

import molsysmt as msm
import numpy as np
import numpy.linalg as la
import smonitor
from argdigest import arg_digest
from depdigest import dep_digest

from elastnetmt import pyunitwizard as puw
from elastnetmt._private.arguments import invalid
from elastnetmt._private.contacts import validate_node_coordinates
from elastnetmt._private.engines import (
    build_hessian_parallel,
    diagonalize_gpu,
    select_engine,
)
from elastnetmt._private.spectral import validate_spectrum
from elastnetmt.model.elastic_network_model import ElasticNetworkModel


class AnisotropicNetworkModel(ElasticNetworkModel):
    """Calculate directional modes of a fully constrained unit-spring network.

    The Hessian uses coordinates converted explicitly to nanometers. With
    normalized springs, eigenvalues and mode vectors are dimensionless;
    derived spectral frequencies are not physical frequencies.

    Attributes
    ----------
    hessian_matrix : numpy.ndarray or None
        Matrix of shape (3 * n_nodes, 3 * n_nodes) after a successful solve.
    engine : str
        Requested construction/decomposition engine.
    engine_used : str or None
        Resolved engine after a successful solve.
    stiffness : None
        Physical stiffness calibration is currently unimplemented.

    Examples
    --------
    >>> from importlib.resources import as_file, files
    >>> from elastnetmt import AnisotropicNetworkModel
    >>> resource = files('molsysmt').joinpath('data/pdb/1tcd.pdb')
    >>> with as_file(resource) as path:
    ...     anm = AnisotropicNetworkModel(str(path), engine='vectorized')
    >>> assert anm.get_modes().shape == (3 * anm.n_nodes - 6, anm.n_nodes, 3)
    >>> assert anm.get_eigenvalues().shape == (3 * anm.n_nodes - 6,)
    """

    _minimum_nodes = 3

    @arg_digest()
    def __init__(
        self,
        molecular_system,
        selection='atom_name=="CA"',
        structure_index=0,
        cutoff="12 angstroms",
        stiffness=None,
        engine="auto",
        syntax="MolSysMT",
    ):
        """Initialize an ANM model with lazy spectral evaluation.

        Parameters
        ----------
        molecular_system : object
            Molecular system in a form supported by MolSysMT.
        selection : str, default='atom_name=="CA"'
            Node expression; at least three finite, distinct nodes are required.
        structure_index : int, default=0
            Zero-based input structure index.
        cutoff : str or quantity, default='12 angstroms'
            Finite positive scalar length defining contacts.
        stiffness : None, default=None
            Reserved for physical spring calibration. Other values are rejected.
        engine : {'auto', 'vectorized', 'parallel', 'gpu'}, default='auto'
            Auto uses Numba when discoverable and NumPy otherwise. Parallel
            requires Numba; GPU requires CuPy. Explicit failures propagate.
        syntax : str, default='MolSysMT'
            Node-selection language.

        Raises
        ------
        elastnetmt.ArgumentError
            If arguments or selected coordinates are invalid.

        Notes
        -----
        A solved ANM must have exactly six numerical rigid zero modes.
        Connectivity alone does not establish geometric rigidity.
        """
        super().__init__(
            molecular_system,
            selection=selection,
            structure_index=structure_index,
            cutoff=cutoff,
            syntax=syntax,
        )
        self.hessian_matrix = None
        self.stiffness = stiffness
        self.engine = engine
        self.engine_used = None

    def _solve(self):
        if self._eigenvalues is not None:
            return
        t_start = time.time()
        coordinates = msm.get(
            self.molecular_system,
            element="atom",
            selection=self.atom_indices,
            structure_indices=0,
            coordinates=True,
        )
        coords = validate_node_coordinates(
            puw.get_value(coordinates[0], to_unit="nanometers"),
            minimum_nodes=self._minimum_nodes,
        )
        engine_to_use = select_engine(self.engine)
        if engine_to_use == "parallel":
            matrix = build_hessian_parallel(coords, self.contacts, self.n_nodes)
        else:
            matrix = self._build_hessian_vectorized(coords)
        if engine_to_use == "gpu":
            values, vectors = diagonalize_gpu(matrix)
        else:
            values, vectors = la.eigh(matrix)

        raw_values = values
        values, vectors = validate_spectrum(
            values, vectors, expected_zero_modes=6, model="ANM"
        )
        raw_max_rigid_ev = float(np.max(np.abs(raw_values[:6])))

        smonitor.emit(
            "DEBUG",
            "elastnetmt.model.spectral_stats",
            source="elastnetmt.model.AnisotropicNetworkModel",
            extra={
                "max_rigid_ev": raw_max_rigid_ev,
                "first_vibrational_ev": float(values[6]),
                "spectral_gap": float(values[6] - values[5]),
            },
        )

        n_modes = 3 * self.n_nodes
        modes = vectors.T.reshape(n_modes, self.n_nodes, 3)[6:]
        t_end = time.time()
        smonitor.emit(
            "INFO",
            "elastnetmt.model.make_model",
            source="elastnetmt.model.AnisotropicNetworkModel",
            extra={
                "engine": engine_to_use,
                "nodes": self.n_nodes,
                "time": t_end - t_start,
            },
        )
        self.hessian_matrix = matrix
        self._eigenvalues, self._eigenvectors = values, vectors
        self._frequencies = np.sqrt(values[6:])
        self._modes = modes
        self.engine_used = engine_to_use

    def _reset_spectral_results(self):
        super()._reset_spectral_results()
        self.hessian_matrix = None

    def _build_hessian_vectorized(self, coords):
        n = self.n_nodes
        hessian = np.zeros((3 * n, 3 * n), dtype=float)
        diffs = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
        dist2 = np.sum(diffs**2, axis=2)
        outer_prods = np.einsum("ijk,ijg->ijkg", diffs, diffs)
        mask = self.contacts
        h_off_diag = np.zeros((n, n, 3, 3))
        idx_i, idx_j = np.where(mask)
        if len(idx_i) > 0:
            h_off_diag[idx_i, idx_j] = (
                -outer_prods[idx_i, idx_j] / dist2[idx_i, idx_j, np.newaxis, np.newaxis]
            )
        for k in range(3):
            for g in range(3):
                hessian[k::3, g::3] = h_off_diag[:, :, k, g]
        h_diag_sum = -np.sum(h_off_diag, axis=1)
        for k in range(3):
            for g in range(3):
                hessian[k::3, g::3] += np.diag(h_diag_sum[:, k, g])
        return hessian

    def get_eigenvalues(self, include_rigid_modes=False):
        """Return ascending dimensionless Hessian eigenvalues.

        Parameters
        ----------
        include_rigid_modes : bool, default=False
            Include the six leading rigid zeros when true.

        Returns
        -------
        numpy.ndarray
            Shape (3 * n_nodes - 6,) by default, or (3 * n_nodes,) including
            rigid modes. Treat this cached array/view as read-only.

        Raises
        ------
        elastnetmt.DegenerateNetworkError
            If the network has additional unconstrained motions.
        elastnetmt.InvalidSpectrumError
            If the numerical decomposition violates the spectrum contract.
        ImportError
            If the requested optional engine cannot be loaded.
        """
        self._solve()
        if include_rigid_modes:
            return self._eigenvalues
        return self._eigenvalues[6:]

    def get_modes(self):
        """Return dimensionless directional modes without rigid motions.

        Returns
        -------
        numpy.ndarray
            Shape ``(3 * n_nodes - 6, n_nodes, 3)``. Mode k corresponds to get_eigenvalues()[k]. Node order follows
            atom_indices. Treat the cached array as read-only.

        Raises
        ------
        elastnetmt.DegenerateNetworkError
            If the network is disconnected or geometrically underconstrained.
        elastnetmt.InvalidSpectrumError
            If eigenpairs are invalid.

        Notes
        -----
        Mode indexing is zero-based after removing six rigid modes. Eigenvector
        signs and bases within degenerate subspaces may vary between backends.
        """
        self._solve()
        return self._modes

    @dep_digest("lindelint")
    @arg_digest()
    def trajectory_along_mode(
        self,
        mode=0,
        selection="all",
        amplitude="6.0 angstroms",
        oscillation_steps=60,
        syntax="MolSysMT",
        interpolation_engine="vectorized",
    ):
        """Generate sinusoidal target-atom displacements along one ANM mode.

        Parameters
        ----------
        mode : int, default=0
            Zero-based non-rigid mode index, as returned by get_modes().
        selection : str, default='all'
            Target atoms for interpolation, independent of the node selection.
        amplitude : str or quantity, default='6.0 angstroms'
            Finite nonnegative maximum target-atom displacement with length units.
        oscillation_steps : int, default=60
            Positive number of frames in one cycle, with the endpoint excluded.
        syntax : str, default='MolSysMT'
            Target-selection language.
        interpolation_engine : {'auto', 'vectorized', 'parallel', 'gpu'}, default='vectorized'
            LinDelINT engine, independent of the model engine. Explicit choices
            are forwarded to the provider; backend failures propagate.

        Returns
        -------
        molsysmt.MolSys
            Selected target atoms with oscillation_steps structures. Coordinates
            are generated in nanometers; the initial model is unchanged.

        Raises
        ------
        elastnetmt.ArgumentError
            If mode, target selection, amplitude or frame count is invalid.
        elastnetmt.DegenerateNetworkError
            If the node network is underconstrained.
        elastnetmt.InvalidSpectrumError
            If the model decomposition is invalid.
        ImportError
            If LinDelINT or a requested optional backend cannot be loaded.

        Notes
        -----
        Normalize the interpolated direction by its maximum target-atom norm,
        then apply amplitude once. The sampled maximum equals amplitude when
        the frame grid includes a sine extremum, for example with eight frames.
        The vectorized default is the tracked workaround for lindelint#8.
        """
        from lindelint import Interpolator

        self._solve()
        if mode >= len(self._modes):
            invalid("mode", f"an index smaller than {len(self._modes)}")
        coords_nodes = msm.get(
            self.molecular_system,
            element="atom",
            selection=self.atom_indices,
            coordinates=True,
        )
        coords_nodes = puw.get_value(coords_nodes[0], to_unit="nanometers")
        mode_vec = self._modes[mode]
        target_indices = msm.select(
            self.molecular_system, selection=selection, syntax=syntax
        )
        if len(target_indices) == 0:
            invalid("selection", "at least one target atom")
        target_system = msm.extract(self.molecular_system, selection=target_indices)
        coords_target = msm.get(
            target_system, element="atom", selection="all", coordinates=True
        )
        coords_target_val = puw.get_value(coords_target[0], to_unit="nanometers")
        # Deterministic CPU default while lindelint#8 owns automatic fallback.
        # Explicit alternatives are passed through unchanged to the provider.
        interp = Interpolator(coords_nodes, mode_vec, engine=interpolation_engine)
        interpolated_mode = interp.do_your_thing(coords_target_val)
        coords_target_nm = puw.get_value(coords_target[0], to_unit="nanometers")
        # Eigenvectors are dimensionless: normalize their interpolated direction
        # and apply the explicit physical amplitude once.
        interpolated_mode_nm = np.asarray(interpolated_mode, dtype=float)
        amplitude_val = puw.get_value(amplitude, to_unit="nanometers")
        max_mode_norm = np.max(np.linalg.norm(interpolated_mode_nm, axis=1))
        factor = amplitude_val / max_mode_norm if max_mode_norm > 0 else 0.0
        frames = []
        for step in range(oscillation_steps):
            phase = 2.0 * np.pi * step / oscillation_steps
            displacement = factor * np.sin(phase) * interpolated_mode_nm
            frames.append(coords_target_nm + displacement)
        new_coords = puw.quantity(np.array(frames), "nanometers")
        target_system = msm.remove(target_system, structure_indices=0)
        msm.append_structures(target_system, new_coords)
        smonitor.emit(
            "INFO",
            "elastnetmt.model.trajectory",
            source="elastnetmt.model.AnisotropicNetworkModel",
            extra={
                "interpolation_engine": interp.engine_type,
                "mode": mode,
                "amplitude_nm": float(amplitude_val),
                "n_frames": oscillation_steps,
            },
        )
        return target_system
