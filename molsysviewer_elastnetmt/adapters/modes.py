from __future__ import annotations

from typing import Any

import numpy as np

from elastnetmt import pyunitwizard as puw
from elastnetmt.model.anisotropic_network_model import AnisotropicNetworkModel

from ..runtime import (
    ensure_runtime,
    record_event,
    set_overlay_visibility,
    update_overlay_parameters,
)


def get_or_build_anm_model(
    view: Any,
    *,
    molecular_system: Any | None = None,
    selection: str | None = None,
    structure_index: int = 0,
    cutoff: Any | None = None,
    syntax: str = "MolSysMT",
) -> AnisotropicNetworkModel:
    runtime = ensure_runtime(view)
    if molecular_system is None:
        molecular_system = getattr(view, "molecular_system", None)
    if molecular_system is None:
        raise ValueError(
            "A molecular system must be loaded in the view before rendering ElastNetMT modes."
        )

    selection = selection or runtime.selection
    cutoff = cutoff or runtime.cutoff

    cache_key = f"anm:{selection}:{cutoff}:{structure_index}:{syntax}"
    model = runtime.cached_models.get(cache_key)
    if model is None:
        model = AnisotropicNetworkModel(
            molecular_system,
            selection=selection,
            structure_index=structure_index,
            cutoff=cutoff,
            syntax=syntax,
        )
        runtime.cached_models[cache_key] = model
        record_event(
            view,
            "build_anm_model",
            selection=selection,
            cutoff=str(cutoff),
            structure_index=structure_index,
        )
    return model


def build_mode_vectors(
    model: AnisotropicNetworkModel, mode_index: int = 0
) -> np.ndarray:
    modes = model.get_modes()
    if mode_index < 0 or mode_index >= modes.shape[0]:
        raise IndexError(
            f"mode_index {mode_index} out of range for {modes.shape[0]} ANM modes."
        )
    return np.asarray(modes[mode_index], dtype=float)


def render_mode_vectors(
    view: Any,
    *,
    molecular_system: Any | None = None,
    selection: str | None = None,
    structure_index: int = 0,
    cutoff: Any | None = None,
    syntax: str = "MolSysMT",
    mode_index: int | None = None,
    length_scale: float = 1.0,
    radius_scale: float = 0.05,
    color_mode: str = "norm",
    color_component: int = 2,
    tag: str | None = None,
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
    if mode_index is None:
        mode_index = runtime.active_mode_index

    vectors = build_mode_vectors(model, mode_index=mode_index)
    tag = tag or f"elastnetmt:mode:{mode_index}"
    layer = view.shapes.add_displacement_vectors(
        origins=None,
        atom_indices=model.atom_indices,
        vectors=puw.quantity(vectors, "angstroms"),
        length_scale=length_scale,
        radius_scale=radius_scale,
        color_mode=color_mode,
        color_component=color_component,
        tag=tag,
    )
    runtime.active_mode_index = int(mode_index)
    runtime.model_kind = "anm"
    set_overlay_visibility(runtime, tag, True)
    update_overlay_parameters(
        runtime,
        tag,
        kind="mode-vectors",
        mode_index=int(mode_index),
        selection=selection or runtime.selection,
        cutoff=str(cutoff or runtime.cutoff),
        structure_index=int(structure_index),
        n_vectors=int(vectors.shape[0]),
    )
    record_event(
        view,
        "render_mode_vectors",
        tag=tag,
        mode_index=int(mode_index),
        n_vectors=int(vectors.shape[0]),
    )
    return layer, model, vectors
