import time

import molsysmt as msm
import numpy as np
import numpy.linalg as la
import smonitor
from argdigest import arg_digest
from depdigest import dep_digest

from elastnetmt import pyunitwizard as puw
from elastnetmt.model.elastic_network_model import ElasticNetworkModel

# Numba Kernel for Hessian Construction
try:
    from numba import njit, prange

    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

if HAS_NUMBA:

    @njit(parallel=True)
    def _build_hessian_numba(coords, contacts, n_nodes):
        hessian = np.zeros((3 * n_nodes, 3 * n_nodes), dtype=np.float64)
        for i in prange(n_nodes):
            for j in range(n_nodes):
                if i == j:
                    continue
                if contacts[i, j]:
                    dx = coords[i, 0] - coords[j, 0]
                    dy = coords[i, 1] - coords[j, 1]
                    dz = coords[i, 2] - coords[j, 2]
                    r2 = dx * dx + dy * dy + dz * dz
                    h00 = -dx * dx / r2
                    h01 = -dx * dy / r2
                    h02 = -dx * dz / r2
                    h11 = -dy * dy / r2
                    h12 = -dy * dz / r2
                    h22 = -dz * dz / r2
                    hessian[3 * i, 3 * j] = h00
                    hessian[3 * i, 3 * j + 1] = h01
                    hessian[3 * i, 3 * j + 2] = h02
                    hessian[3 * i + 1, 3 * j] = h01
                    hessian[3 * i + 1, 3 * j + 1] = h11
                    hessian[3 * i + 1, 3 * j + 2] = h12
                    hessian[3 * i + 2, 3 * j] = h02
                    hessian[3 * i + 2, 3 * j + 1] = h12
                    hessian[3 * i + 2, 3 * j + 2] = h22
                    hessian[3 * i, 3 * i] -= h00
                    hessian[3 * i, 3 * i + 1] -= h01
                    hessian[3 * i, 3 * i + 2] -= h02
                    hessian[3 * i + 1, 3 * i] -= h01
                    hessian[3 * i + 1, 3 * i + 1] -= h11
                    hessian[3 * i + 1, 3 * i + 2] -= h12
                    hessian[3 * i + 2, 3 * i] -= h02
                    hessian[3 * i + 2, 3 * i + 1] -= h12
                    hessian[3 * i + 2, 3 * i + 2] -= h22
        return hessian


class AnisotropicNetworkModel(ElasticNetworkModel):
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
        coords = puw.get_value(coordinates[0])
        engine_to_use = self.engine
        if engine_to_use == "auto":
            engine_to_use = "parallel" if HAS_NUMBA else "vectorized"
        if engine_to_use == "parallel" and HAS_NUMBA:
            self.hessian_matrix = _build_hessian_numba(
                coords, self.contacts, self.n_nodes
            )
        else:
            self.hessian_matrix = self._build_hessian_vectorized(coords)
        if engine_to_use == "gpu":
            try:
                import cupy as cp

                h_gpu = cp.asarray(self.hessian_matrix)
                e_gpu, v_gpu = cp.linalg.eigh(h_gpu)
                self._eigenvalues = cp.asnumpy(e_gpu)
                self._eigenvectors = cp.asnumpy(v_gpu)
            except ImportError:
                self._eigenvalues, self._eigenvectors = la.eigh(self.hessian_matrix)
        else:
            self._eigenvalues, self._eigenvectors = la.eigh(self.hessian_matrix)
        if self.n_nodes > 2 and np.isclose(self._eigenvalues[6], 0.0, atol=1e-8):
            smonitor.emit_from_catalog(
                "ENM-E020", source="elastnetmt.model.AnisotropicNetworkModel"
            )
        if np.any(self._eigenvalues[6:] < -1e-6):
            smonitor.emit_from_catalog(
                "ENM-E030",
                min_ev=float(np.min(self._eigenvalues)),
                source="elastnetmt.model.AnisotropicNetworkModel",
            )

        smonitor.emit(
            "DEBUG",
            "elastnetmt.model.spectral_stats",
            source="elastnetmt.model.AnisotropicNetworkModel",
            extra={
                "max_rigid_ev": float(np.max(np.abs(self._eigenvalues[:6]))),
                "first_vibrational_ev": float(self._eigenvalues[6]),
                "spectral_gap": float(self._eigenvalues[6] - self._eigenvalues[5]),
            },
        )

        self._frequencies = np.sqrt(np.absolute(self._eigenvalues[6:]))
        n_modes = 3 * self.n_nodes
        self._modes = self._eigenvectors.T.reshape(n_modes, self.n_nodes, 3)
        self._modes = self._modes[6:]
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
        self._solve()
        if include_rigid_modes:
            return self._eigenvalues
        return self._eigenvalues[6:]

    def get_modes(self):
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
    ):
        from lindelint import Interpolator

        self._solve()
        coords_nodes = msm.get(
            self.molecular_system,
            element="atom",
            selection=self.atom_indices,
            coordinates=True,
        )
        coords_nodes = puw.get_value(coords_nodes[0])
        mode_vec = self._modes[mode]
        target_indices = msm.select(
            self.molecular_system, selection=selection, syntax=syntax
        )
        target_system = msm.extract(self.molecular_system, selection=target_indices)
        coords_target = msm.get(
            target_system, element="atom", selection="all", coordinates=True
        )
        coords_target_val = puw.get_value(coords_target[0])
        interp = Interpolator(coords_nodes, mode_vec)
        interpolated_mode = interp.do_your_thing(coords_target_val)
        coords_target_nm = puw.get_value(coords_target[0], to_unit="nanometers")
        interpolated_mode_nm = puw.convert(
            puw.quantity(interpolated_mode, "angstroms"), to_unit="nanometers"
        )
        interpolated_mode_nm = puw.get_value(interpolated_mode_nm)
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
        return target_system
