import time

import molsysmt as msm
import numpy as np
import numpy.linalg as la
import smonitor
from argdigest import arg_digest
from depdigest import dep_digest

from elastnetmt import pyunitwizard as puw
from elastnetmt._private.arguments import invalid
from elastnetmt._private.engines import (
    build_kirchhoff_parallel,
    diagonalize_gpu,
    select_engine,
)
from elastnetmt._private.smonitor import emit_catalog
from elastnetmt.model.elastic_network_model import ElasticNetworkModel


class GaussianNetworkModel(ElasticNetworkModel):
    """
    Gaussian Network Model (GNM) implementation.
    """

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
        self.engine_used = engine_to_use

        if engine_to_use == "parallel":
            self.kirchhoff_matrix = build_kirchhoff_parallel(
                self.contacts, self.n_nodes
            )
        else:
            self.kirchhoff_matrix = -self.contacts.astype(float)
            np.fill_diagonal(self.kirchhoff_matrix, self.contacts.sum(axis=1))

        if engine_to_use == "gpu":
            self._eigenvalues, self._eigenvectors = diagonalize_gpu(
                self.kirchhoff_matrix
            )
        else:
            self._eigenvalues, self._eigenvectors = la.eigh(self.kirchhoff_matrix)

        if self.n_nodes > 1 and np.isclose(self._eigenvalues[1], 0.0, atol=1e-8):
            emit_catalog("ENM-E020", source="elastnetmt.model.GaussianNetworkModel")

        self._frequencies = np.sqrt(np.absolute(self._eigenvalues))
        self._modes = np.transpose(self._eigenvectors)

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
        return self._get_unscaled_b_factors(n_modes) * self.scaling_factor

    def _get_unscaled_b_factors(self, n_modes="all"):
        """Calculate the uncalibrated diagonal of the Kirchhoff pseudoinverse."""
        self._solve()
        if n_modes == "all":
            n_modes = self.n_nodes
        else:
            n_modes = min(n_modes + 1, self.n_nodes)
        inv_ev = 1.0 / self._eigenvalues[1:n_modes]
        self.b_factors_theo = np.einsum(
            "ik,k->i", self._eigenvectors[:, 1:n_modes] ** 2, inv_ev
        )
        return self.b_factors_theo

    def fit_to_experimental_b_factors(self):
        """Fit unscaled predictions to experimental B factors in square angstroms.

        Repeated fitting of an unchanged network produces the same scale and
        Pearson correlation. Returns a scalar scale and scalar correlation.
        """
        exp_b = msm.get(
            self.molecular_system,
            element="atom",
            selection=self.atom_indices,
            b_factor=True,
        )
        self.b_factors_exp = np.asarray(
            puw.get_value(exp_b, to_unit="angstroms**2"), dtype=float
        ).reshape(-1)
        theo_b = self._get_unscaled_b_factors()
        self.scaling_factor = float(
            np.dot(self.b_factors_exp, theo_b) / np.dot(theo_b, theo_b)
        )
        correlation = np.corrcoef(self.b_factors_exp, theo_b)[0, 1]
        if correlation < 0.5:
            emit_catalog(
                "ENM-W010",
                correlation=float(correlation),
                source="elastnetmt.model.GaussianNetworkModel",
            )
        return self.scaling_factor, correlation

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
        lower = puw.get_value(min_cutoff, to_unit="angstroms")
        upper = puw.get_value(max_cutoff, to_unit="angstroms")
        if not 0 < lower < upper:
            invalid("min_cutoff/max_cutoff", "0 < min_cutoff < max_cutoff")
        cutoffs = np.linspace(
            lower,
            upper,
            steps,
        )
        best_corr = -1.0
        best_cutoff = None
        for c in cutoffs:
            self.calculate_contacts(cutoff=f"{c} angstroms")
            _, corr = self.fit_to_experimental_b_factors()
            if corr > best_corr:
                best_corr = corr
                best_cutoff = c
        self.calculate_contacts(cutoff=f"{best_cutoff} angstroms")
        self.fit_to_experimental_b_factors()
        return puw.quantity(best_cutoff, "angstroms"), best_corr
