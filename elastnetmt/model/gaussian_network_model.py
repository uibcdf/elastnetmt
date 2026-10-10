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
    """
    Gaussian Network Model (GNM) implementation.
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
        self._solve()
        return self._eigenvalues

    def get_eigenvectors(self):
        self._solve()
        return self._eigenvectors

    @arg_digest()
    def get_b_factors(self, n_modes="all"):
        """Return fitted B-factor magnitudes in square angstroms.

        Before fitting, values are the dimensionless spectral prediction with
        scaling factor one. ``b_factors_theo`` always retains that unscaled
        prediction. ``n_modes`` counts non-rigid modes; ``"all"`` uses all of them.
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
