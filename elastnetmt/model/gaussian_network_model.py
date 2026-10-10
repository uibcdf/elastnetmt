import time

import molsysmt as msm
import numpy as np
import numpy.linalg as la
import smonitor
from argdigest import arg_digest
from depdigest import dep_digest

from elastnetmt import pyunitwizard as puw
from elastnetmt._private.arguments import invalid
from elastnetmt._private.b_factors import experimental_profile, fit_profiles
from elastnetmt._private.contacts import get_contacts
from elastnetmt._private.engines import (
    build_kirchhoff_parallel,
    diagonalize_gpu,
    select_engine,
)
from elastnetmt._private.smonitor import (
    CutoffOptimizationError,
    DegenerateNetworkError,
    InvalidSpectrumError,
    UndefinedCorrelationError,
    emit_catalog,
)
from elastnetmt._private.spectral import validate_spectrum
from elastnetmt.model.elastic_network_model import ElasticNetworkModel


class GaussianNetworkModel(ElasticNetworkModel):
    """Calculate isotropic fluctuations from a connected unit-spring network.

    GNM diagonalizes the normalized Kirchhoff matrix. Eigenvalues and the
    uncalibrated pseudoinverse diagonal are dimensionless. Experimental
    B factors provide a separate fitted scale in square angstroms.

    Attributes
    ----------
    kirchhoff_matrix : numpy.ndarray or None
        Matrix of shape (n_nodes, n_nodes), available after a successful solve.
    engine : str
        Requested construction/decomposition engine.
    engine_used : str or None
        Resolved engine after a successful solve.
    scaling_factor : float
        One before fitting; fitted square-angstrom scale afterward.
    b_factors_theo : numpy.ndarray or None
        Most recently calculated unscaled prediction, one value per node.
    b_factors_exp : numpy.ndarray or None
        Experimental magnitudes in square angstroms after a successful fit.

    Examples
    --------
    >>> import numpy as np
    >>> from importlib.resources import as_file, files
    >>> from elastnetmt import GaussianNetworkModel
    >>> resource = files('molsysmt').joinpath('data/pdb/1tcd.pdb')
    >>> with as_file(resource) as path:
    ...     gnm = GaussianNetworkModel(str(path), engine='vectorized')
    >>> raw = gnm.get_b_factors()
    >>> assert raw.shape == (gnm.n_nodes,)
    >>> scale, correlation = gnm.fit_to_experimental_b_factors()
    >>> np.testing.assert_allclose(gnm.get_b_factors(), raw * scale)
    """

    _minimum_nodes = 2

    @arg_digest()
    def __init__(
        self,
        molecular_system,
        selection='atom_name=="CA"',
        structure_index=0,
        cutoff="7 angstroms",
        engine="auto",
        syntax="MolSysMT",
    ):
        """Initialize a GNM model with lazy spectral evaluation.

        Parameters
        ----------
        molecular_system : object
            Molecular system in a form supported by MolSysMT.
        selection : str, default='atom_name=="CA"'
            Node selection; at least two finite, distinct positions are required.
        structure_index : int, default=0
            Zero-based input structure index.
        cutoff : str or quantity, default='7 angstroms'
            Finite positive scalar length defining contacts.
        engine : {'auto', 'vectorized', 'parallel', 'gpu'}, default='auto'
            Auto uses Numba when discoverable and NumPy otherwise. Parallel
            requires Numba; GPU requires CuPy. Explicit failures propagate.
        syntax : str, default='MolSysMT'
            Node-selection language.

        Raises
        ------
        elastnetmt.ArgumentError
            If input values or selected coordinates are invalid.

        Notes
        -----
        Eigenpairs are evaluated on first query. A connected GNM must have
        exactly one numerical zero mode; disconnected spectra are rejected.
        """

        super().__init__(
            molecular_system,
            selection=selection,
            structure_index=structure_index,
            cutoff=cutoff,
            syntax=syntax,
        )

        self.kirchhoff_matrix = None
        self.engine = engine
        self.engine_used = None
        self.scaling_factor = 1.0
        self.b_factors_theo = None
        self.b_factors_exp = None

    def _solve(self):
        """Builds the Kirchhoff matrix and performs spectral analysis."""
        if self._eigenvalues is not None:
            return

        t_start = time.time()
        engine_to_use = select_engine(self.engine)

        if engine_to_use == "parallel":
            matrix = build_kirchhoff_parallel(self.contacts, self.n_nodes)
        else:
            matrix = -self.contacts.astype(float)
            np.fill_diagonal(matrix, self.contacts.sum(axis=1))

        if engine_to_use == "gpu":
            values, vectors = diagonalize_gpu(matrix)
        else:
            values, vectors = la.eigh(matrix)

        values, vectors = validate_spectrum(
            values, vectors, expected_zero_modes=1, model="GNM"
        )

        t_end = time.time()
        smonitor.emit(
            "INFO",
            "elastnetmt.model.make_model",
            source="elastnetmt.model.GaussianNetworkModel",
            extra={
                "engine": engine_to_use,
                "nodes": self.n_nodes,
                "time": t_end - t_start,
            },
        )
        self.kirchhoff_matrix = matrix
        self._eigenvalues, self._eigenvectors = values, vectors
        self._frequencies = np.sqrt(values)
        self._modes = vectors.T
        self.engine_used = engine_to_use

    def get_eigenvalues(self):
        """Return ascending dimensionless Kirchhoff eigenvalues.

        Returns
        -------
        numpy.ndarray
            Shape ``(n_nodes,)``. Eigenvalues including the leading rigid zero mode.

        Raises
        ------
        elastnetmt.DegenerateNetworkError
            If the network has more than one numerical zero mode.
        elastnetmt.InvalidSpectrumError
            If the backend decomposition violates the spectrum contract.
        ImportError
            If the requested optional engine cannot be loaded.

        Notes
        -----
        Treat this cached array as read-only. Rebuilding contacts invalidates it.
        """
        self._solve()
        return self._eigenvalues

    def get_eigenvectors(self):
        """Return dimensionless eigenvectors as columns in eigenvalue order.

        Returns
        -------
        numpy.ndarray
            Shape ``(n_nodes, n_nodes)``. Column zero is the rigid mode. Column k belongs to eigenvalue k.

        Raises
        ------
        elastnetmt.DegenerateNetworkError
            If the network is disconnected.
        elastnetmt.InvalidSpectrumError
            If decomposition results are invalid.

        Notes
        -----
        Treat this cached array as read-only. Signs and the basis within a
        degenerate eigenspace may differ between numerical backends.
        """
        self._solve()
        return self._eigenvectors

    @arg_digest()
    def get_b_factors(self, n_modes="all"):
        """Return raw fluctuations or calibrated B-factor magnitudes.

        Before fitting, values are the dimensionless spectral prediction with
        scaling factor one. ``b_factors_theo`` always retains that unscaled
        prediction. ``n_modes`` counts non-rigid modes; ``"all"`` uses all of them.

        Parameters
        ----------
        n_modes : int or {'all'}, default='all'
            Positive number of lowest non-rigid modes; capped at n_nodes - 1.

        Returns
        -------
        numpy.ndarray
            Shape ``(n_nodes,)``. Plain magnitudes: dimensionless before fitting, square angstroms
            afterward. The result is not a PyUnitWizard quantity.

        Raises
        ------
        elastnetmt.ArgumentError
            If n_modes is invalid.
        elastnetmt.DegenerateNetworkError
            If the network is disconnected.
        elastnetmt.InvalidSpectrumError
            If eigenpairs, their inverse or the prediction are unrepresentable.

        Notes
        -----
        The fitted scale always uses the complete spectrum. Changing n_modes
        applies that same scale to a truncated spectral prediction.
        """
        with self._restore_state_on_failure():
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                try:
                    result = self._get_unscaled_b_factors(n_modes) * self.scaling_factor
                except FloatingPointError as exc:
                    raise InvalidSpectrumError(
                        extra={
                            "model": "GNM",
                            "reason": "B-factor prediction exceeds the numerical range",
                        }
                    ) from exc
            if not np.all(np.isfinite(result)):
                raise InvalidSpectrumError(
                    extra={
                        "model": "GNM",
                        "reason": "the B-factor prediction is nonfinite",
                    }
                )
            return result

    def _get_unscaled_b_factors(self, n_modes="all"):
        """Calculate the uncalibrated diagonal of the Kirchhoff pseudoinverse."""
        self._solve()
        if n_modes == "all":
            n_modes = self.n_nodes
        else:
            n_modes = min(n_modes + 1, self.n_nodes)
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            try:
                inv_ev = 1.0 / self._eigenvalues[1:n_modes]
                prediction = np.einsum(
                    "ik,k->i", self._eigenvectors[:, 1:n_modes] ** 2, inv_ev
                )
            except FloatingPointError as exc:
                raise InvalidSpectrumError(
                    extra={
                        "model": "GNM",
                        "reason": "spectral inversion exceeds the numerical range",
                    }
                ) from exc
        if not np.all(np.isfinite(prediction)):
            raise InvalidSpectrumError(
                extra={"model": "GNM", "reason": "the spectral prediction is nonfinite"}
            )
        self.b_factors_theo = prediction
        return self.b_factors_theo

    def fit_to_experimental_b_factors(self):
        """Fit unscaled predictions to experimental B factors in square angstroms.

        Repeated fitting of an unchanged network produces the same scale and
        Pearson correlation. Returns a scalar scale and scalar correlation.

        Both profiles must be finite, nonnegative and varying. A failed fit
        retains the previous calibration and caches.

        Returns
        -------
        scale : float
            Least-squares multiplier from raw fluctuations to square angstroms.
        correlation : float
            Pearson correlation in [-1, 1].

        Raises
        ------
        elastnetmt.ArgumentError
            If experimental values are missing, invalid or unrepresentable.
        elastnetmt.UndefinedCorrelationError
            If either profile is numerically constant.
        elastnetmt.DegenerateNetworkError
            If the network is disconnected.
        elastnetmt.InvalidSpectrumError
            If the spectral prediction is invalid.
        """
        with self._restore_state_on_failure():
            return self._fit_to_profile(self._experimental_profile())

    def _experimental_profile(self):
        exp_b = msm.get(
            self.molecular_system,
            element="atom",
            selection=self.atom_indices,
            b_factor=True,
        )
        return experimental_profile(exp_b, n_nodes=self.n_nodes)

    def _fit_to_profile(self, experimental):
        """Fit one validated experimental snapshot and publish only a completed fit."""
        theo_b = self._get_unscaled_b_factors()
        scale, correlation = fit_profiles(experimental, theo_b)
        if correlation < 0.5:
            emit_catalog(
                "ENM-W010",
                correlation=float(correlation),
                source="elastnetmt.model.GaussianNetworkModel",
            )
        self.scaling_factor = scale
        self.b_factors_exp = experimental.copy()
        return scale, correlation

    def _reset_spectral_results(self):
        """A changed network invalidates its spectral prediction and calibration."""
        super()._reset_spectral_results()
        self.kirchhoff_matrix = None
        self.scaling_factor = 1.0
        self.b_factors_theo = None
        self.b_factors_exp = None

    @dep_digest("matplotlib")
    @arg_digest()
    def show_b_factors(self, show_experimental=True, title="B-factors Profile"):
        """Plot predicted fluctuations and optionally experimental B factors.

        Parameters
        ----------
        show_experimental : bool, default=True
            Fit first when necessary and overlay experimental values.
        title : str, default='B-factors Profile'
            Nonempty figure title.

        Returns
        -------
        None
            Display through Matplotlib's active backend.

        Raises
        ------
        elastnetmt.ArgumentError
            If arguments or requested experimental values are invalid.
        elastnetmt.UndefinedCorrelationError
            If a requested fit has a constant profile.

        Notes
        -----
        The vertical axis is dimensionless before calibration and square
        angstroms afterward. Plotting applies the calibration scale once.
        """
        import matplotlib.pyplot as plt

        self._solve()
        if show_experimental and self.b_factors_exp is None:
            self.fit_to_experimental_b_factors()
        theo_b = self.get_b_factors()
        plt.figure(figsize=(10, 4))
        plt.plot(theo_b, label="GNM Theoretical", color="blue")
        if show_experimental:
            plt.plot(
                self.b_factors_exp, label="Experimental (PDB)", color="red", alpha=0.6
            )
        plt.xlabel("Node Index")
        plt.ylabel(
            "B-factor ($A^2$)"
            if self.b_factors_exp is not None
            else "Uncalibrated fluctuation (dimensionless)"
        )
        plt.title(title)
        plt.legend()
        return plt.show()

    @arg_digest()
    def get_best_cutoff(
        self, min_cutoff="5 angstroms", max_cutoff="15 angstroms", steps=10
    ):
        """Optimize Pearson correlation on a finite cutoff grid.

        Retain the current node selection. Skip disconnected networks and
        constant theoretical profiles, then refit the winner. Missing/invalid
        experimental data and backend failures propagate. If no candidate is
        admissible, raise CutoffOptimizationError and preserve prior state.

        Parameters
        ----------
        min_cutoff : str or quantity, default='5 angstroms'
            Positive lower endpoint with explicit length units.
        max_cutoff : str or quantity, default='15 angstroms'
            Upper endpoint, strictly larger than min_cutoff.
        steps : int, default=10
            Number of evenly spaced candidates, including endpoints; at least two.

        Returns
        -------
        cutoff : quantity
            Winning threshold in angstroms.
        correlation : float
            Winning Pearson correlation; ties retain the first grid candidate.

        Raises
        ------
        elastnetmt.ArgumentError
            If the grid or experimental values are invalid.
        elastnetmt.UndefinedCorrelationError
            If the experimental profile is constant.
        elastnetmt.CutoffOptimizationError
            If every candidate is degenerate or has a constant theoretical profile.
        elastnetmt.InvalidSpectrumError
            If a candidate's numerical decomposition is invalid.
        """
        lower = puw.get_value(min_cutoff, to_unit="angstroms")
        upper = puw.get_value(max_cutoff, to_unit="angstroms")
        if not 0 < lower < upper:
            invalid("min_cutoff/max_cutoff", "0 < min_cutoff < max_cutoff")
        cutoffs = np.linspace(
            lower,
            upper,
            steps,
        )
        experimental = self._experimental_profile()
        atom_indices = self.atom_indices
        best_corr = -np.inf
        best_cutoff = None
        with self._restore_state_on_failure():
            for c in cutoffs:
                self._contacts_at_cutoff(c, atom_indices)
                try:
                    _, corr = self._fit_to_profile(experimental)
                except DegenerateNetworkError:
                    continue
                except UndefinedCorrelationError as exc:
                    if exc.extra.get("argument") != "theoretical_b_factors":
                        raise
                    continue
                if corr > best_corr:
                    best_corr = corr
                    best_cutoff = c
            if best_cutoff is None:
                raise CutoffOptimizationError()
            self._contacts_at_cutoff(best_cutoff, atom_indices)
            self._fit_to_profile(experimental)
        return puw.quantity(best_cutoff, "angstroms"), best_corr

    def _contacts_at_cutoff(self, cutoff, atom_indices):
        """Rebuild contacts for the currently selected nodes, retaining their indices."""
        contacts, indices, quantity = get_contacts(
            self.molecular_system,
            selection=atom_indices,
            cutoff=puw.quantity(cutoff, "angstroms"),
            minimum_nodes=self._minimum_nodes,
        )
        self._set_contacts(contacts, indices, quantity)
