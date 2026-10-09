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
    build_hessian_parallel,
    diagonalize_gpu,
    select_engine,
)
from elastnetmt._private.smonitor import emit_catalog
from elastnetmt.model.elastic_network_model import ElasticNetworkModel


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
        coords = puw.get_value(coordinates[0], to_unit="nanometers")
        engine_to_use = select_engine(self.engine)
        self.engine_used = engine_to_use
        if engine_to_use == "parallel":
            self.hessian_matrix = build_hessian_parallel(
                coords, self.contacts, self.n_nodes
            )
        else:
            self.hessian_matrix = self._build_hessian_vectorized(coords)
        if engine_to_use == "gpu":
            self._eigenvalues, self._eigenvectors = diagonalize_gpu(self.hessian_matrix)
        else:
            self._eigenvalues, self._eigenvectors = la.eigh(self.hessian_matrix)

        if self.n_nodes > 2 and np.isclose(self._eigenvalues[6], 0.0, atol=1e-8):
            emit_catalog("ENM-E020", source="elastnetmt.model.AnisotropicNetworkModel")
        if np.any(self._eigenvalues[6:] < -1e-6):
            emit_catalog(
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
        interpolation_engine="vectorized",
    ):
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
