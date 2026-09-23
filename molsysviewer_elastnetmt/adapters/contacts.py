from __future__ import annotations

from typing import Any

import numpy as np

from elastnetmt.model.elastic_network_model import ElasticNetworkModel

from ..runtime import (
    ensure_runtime,
    record_event,
    set_overlay_visibility,
    update_overlay_parameters,
)


def build_contact_atom_pairs(model: ElasticNetworkModel) -> list[tuple[int, int]]:
    if model.contacts is None or model.atom_indices is None:
        return []

    rows, cols = np.where(np.triu(model.contacts, k=1))
    atom_indices = np.asarray(model.atom_indices, dtype=int)
    return [
        (int(atom_indices[row]), int(atom_indices[col]))
        for row, col in zip(rows, cols, strict=False)
    ]


def get_or_build_contact_model(
    view: Any,
    *,
    molecular_system: Any | None = None,
    selection: str | None = None,
    structure_index: int = 0,
    cutoff: Any | None = None,
    syntax: str = "MolSysMT",
) -> ElasticNetworkModel:
    runtime = ensure_runtime(view)
    if molecular_system is None:
        molecular_system = getattr(view, "molecular_system", None)
    if molecular_system is None:
        raise ValueError(
            "A molecular system must be loaded in the view before rendering ElastNetMT contacts."
        )

    selection = selection or runtime.selection
    cutoff = cutoff or runtime.cutoff

    cache_key = f"contacts:{selection}:{cutoff}:{structure_index}:{syntax}"
    model = runtime.cached_models.get(cache_key)
    if model is None:
        model = ElasticNetworkModel(
            molecular_system,
            selection=selection,
            structure_index=structure_index,
            cutoff=cutoff,
            syntax=syntax,
        )
        runtime.cached_models[cache_key] = model
        record_event(
            view,
            "build_contact_model",
            selection=selection,
            cutoff=str(cutoff),
            structure_index=structure_index,
        )
    return model


def render_contact_network(
    view: Any,
    *,
    molecular_system: Any | None = None,
    selection: str | None = None,
    structure_index: int = 0,
    cutoff: Any | None = None,
    syntax: str = "MolSysMT",
    radius: Any = "0.2 angstroms",
    color: int = 0x808080,
    alpha: float = 1.0,
    tag: str = "elastnetmt:contacts",
):
    runtime = ensure_runtime(view)
    model = get_or_build_contact_model(
        view,
        molecular_system=molecular_system,
        selection=selection,
        structure_index=structure_index,
        cutoff=cutoff,
        syntax=syntax,
    )
    atom_pairs = build_contact_atom_pairs(model)
    layer = view.shapes.add_links(
        atom_pairs=atom_pairs,
        radius=radius,
        color=color,
        alpha=alpha,
        tag=tag,
    )
    set_overlay_visibility(runtime, tag, True)
    update_overlay_parameters(
        runtime,
        tag,
        kind="contacts",
        selection=selection or runtime.selection,
        cutoff=str(cutoff or runtime.cutoff),
        structure_index=int(structure_index),
        n_links=len(atom_pairs),
    )
    record_event(view, "render_contact_network", tag=tag, n_links=len(atom_pairs))
    return layer, model
