from __future__ import annotations

from typing import Any

import molsysmt as msm
import numpy as np

from ..runtime import (
    ensure_runtime,
    record_event,
    set_overlay_visibility,
    update_overlay_parameters,
)
from .modes import get_or_build_anm_model


def get_node_coordinates(model) -> Any:
    coordinates = msm.get(
        model.molecular_system,
        element="atom",
        selection=model.atom_indices,
        structure_indices=0,
        coordinates=True,
    )
    return coordinates[0]


def build_local_anisotropy_eigendecomposition(model, mode_count: int = 20):
    eigenvalues = np.asarray(model.get_eigenvalues(), dtype=float)
    modes = np.asarray(model.get_modes(), dtype=float)

    if eigenvalues.size == 0 or modes.size == 0:
        raise ValueError("ANM model does not contain vibrational modes.")

    mode_count = max(1, min(int(mode_count), eigenvalues.shape[0], modes.shape[0]))
    selected_values = eigenvalues[:mode_count]
    selected_modes = modes[:mode_count]

    safe_weights = 1.0 / np.clip(selected_values, 1.0e-12, None)
    tensors = np.einsum("mni,mnj,m->nij", selected_modes, selected_modes, safe_weights)

    node_eigenvalues = []
    node_eigenvectors = []
    for tensor in tensors:
        eigvals, eigvecs = np.linalg.eigh(tensor)
        order = np.argsort(eigvals)[::-1]
        node_eigenvalues.append(eigvals[order].tolist())
        node_eigenvectors.append(eigvecs[:, order].T.tolist())

    return node_eigenvalues, node_eigenvectors


def render_anisotropy_ellipsoids(
    view: Any,
    *,
    molecular_system: Any | None = None,
    selection: str | None = None,
    structure_index: int = 0,
    cutoff: Any | None = None,
    syntax: str = "MolSysMT",
    mode_count: int = 20,
    scale: float = 1.0,
    max_eccentricity: float = 5.0,
    color_mode: str = "anisotropy",
    alpha: float = 0.6,
    tag: str = "elastnetmt:anisotropy",
):
    runtime = ensure_runtime(view)
    model = get_or_build_anm_model(
        view,
        molecular_system=molecular_system,
        selection=selection,
        structure_index=structure_index,
        cutoff=cutoff,
        syntax=syntax,
    )
    centers = get_node_coordinates(model)
    eigenvalues, eigenvectors = build_local_anisotropy_eigendecomposition(
        model, mode_count=mode_count
    )
    layer = view.shapes.add_anisotropy_ellipsoids(
        centers=centers,
        eigenvalues=eigenvalues,
        eigenvectors=eigenvectors,
        scale=scale,
        max_eccentricity=max_eccentricity,
        color_mode=color_mode,
        alpha=alpha,
        tag=tag,
        name="ElastNetMT Anisotropy",
    )
    runtime.model_kind = "anm"
    set_overlay_visibility(runtime, tag, True)
    update_overlay_parameters(
        runtime,
        tag,
        kind="anisotropy-ellipsoids",
        mode_count=int(mode_count),
        selection=selection or runtime.selection,
        cutoff=str(cutoff or runtime.cutoff),
        structure_index=int(structure_index),
        n_nodes=int(model.n_nodes),
    )
    record_event(
        view,
        "render_anisotropy_ellipsoids",
        tag=tag,
        mode_count=int(mode_count),
        n_nodes=model.n_nodes,
    )
    return layer, model, eigenvalues, eigenvectors
