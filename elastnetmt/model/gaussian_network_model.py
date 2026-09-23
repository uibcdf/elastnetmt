import time

import molsysmt as msm
import numpy as np
import numpy.linalg as la
import smonitor
from argdigest import arg_digest
from depdigest import dep_digest

from elastnetmt import pyunitwizard as puw
from elastnetmt._private.smonitor import warn
from elastnetmt.model.elastic_network_model import ElasticNetworkModel


def _length_to_angstroms(length):
    if isinstance(length, str):
        stripped = length.strip()
        if stripped.endswith(" A"):
            stripped = f"{stripped[:-2]} angstrom"
        elif stripped == "A":
            stripped = "angstrom"
        length = puw.parse.parse(stripped)
    return puw.get_value(length, to_unit="angstroms")


# Numba Kernel for Kirchhoff Construction
try:
    from numba import njit, prange

    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

if HAS_NUMBA:

    @njit(parallel=True)
    def _build_kirchhoff_numba(contacts, n_nodes):
        kirchhoff = -contacts.astype(np.float64)
        for i in prange(n_nodes):
            row_sum = 0.0
            for j in range(n_nodes):
                if i != j and contacts[i, j]:
                    row_sum += 1.0
            kirchhoff[i, i] = row_sum
        return kirchhoff


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
        self.scaling_factor = 1.0
        self.b_factors_theo = None
        self.b_factors_exp = None

    def _solve(self):
        """Builds the Kirchhoff matrix and performs spectral analysis."""
        if self._eigenvalues is not None:
            return

        t_start = time.time()
        engine_to_use = self.engine
        if engine_to_use == "auto":
            engine_to_use = "parallel" if HAS_NUMBA else "vectorized"

        if engine_to_use == "parallel" and HAS_NUMBA:
            self.kirchhoff_matrix = _build_kirchhoff_numba(self.contacts, self.n_nodes)
        else:
            self.kirchhoff_matrix = -self.contacts.astype(float)
            np.fill_diagonal(self.kirchhoff_matrix, self.contacts.sum(axis=1))

        if engine_to_use == "gpu":
            try:
                import cupy as cp

                k_gpu = cp.asarray(self.kirchhoff_matrix)
                e_gpu, v_gpu = cp.linalg.eigh(k_gpu)
                self._eigenvalues = cp.asnumpy(e_gpu)
                self._eigenvectors = cp.asnumpy(v_gpu)
            except ImportError:
                warn("CuPy not found. Falling back to CPU.")
                self._eigenvalues, self._eigenvectors = la.eigh(self.kirchhoff_matrix)
        else:
            self._eigenvalues, self._eigenvectors = la.eigh(self.kirchhoff_matrix)

        if self.n_nodes > 1 and np.isclose(self._eigenvalues[1], 0.0, atol=1e-8):
            smonitor.emit_from_catalog(
                "ENM-E020", source="elastnetmt.model.GaussianNetworkModel"
            )

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
        self._solve()
        if n_modes == "all":
            n_modes = self.n_nodes
        else:
            n_modes = min(n_modes + 1, self.n_nodes)
        inv_ev = 1.0 / self._eigenvalues[1:n_modes]
        self.b_factors_theo = np.einsum(
            "ik,k->i", self._eigenvectors[:, 1:n_modes] ** 2, inv_ev
        )
        return self.b_factors_theo * self.scaling_factor

    def fit_to_experimental_b_factors(self):
        exp_b = msm.get(
            self.molecular_system,
            element="atom",
            selection=self.atom_indices,
            b_factor=True,
        )
        self.b_factors_exp = puw.get_value(exp_b)
        theo_b = self.get_b_factors()
        self.scaling_factor = np.dot(self.b_factors_exp, theo_b) / np.dot(
            theo_b, theo_b
        )
        correlation = np.corrcoef(self.b_factors_exp, theo_b)[0, 1]
        if correlation < 0.5:
            smonitor.emit_from_catalog(
                "ENM-W010",
                correlation=float(correlation),
                source="elastnetmt.model.GaussianNetworkModel",
            )
        return self.scaling_factor, correlation

    @dep_digest("matplotlib")
    @arg_digest()
    def show_b_factors(self, show_experimental=True, title="B-factors Profile"):
        import matplotlib.pyplot as plt

        self._solve()
        theo_b = self.get_b_factors()
        plt.figure(figsize=(10, 4))
        plt.plot(theo_b * self.scaling_factor, label="GNM Theoretical", color="blue")
        if show_experimental:
            if self.b_factors_exp is None:
                self.fit_to_experimental_b_factors()
            plt.plot(
                self.b_factors_exp, label="Experimental (PDB)", color="red", alpha=0.6
            )
        plt.xlabel("Node Index")
        plt.ylabel("B-factor ($A^2$)")
        plt.title(title)
        plt.legend()
        return plt.show()

    def get_best_cutoff(
        self, min_cutoff="5 angstroms", max_cutoff="15 angstroms", steps=10
    ):
        cutoffs = np.linspace(
            _length_to_angstroms(min_cutoff),
            _length_to_angstroms(max_cutoff),
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
        return puw.quantity(best_cutoff, "angstroms"), best_corr
