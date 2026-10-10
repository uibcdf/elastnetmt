from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, fields
from typing import Any


@dataclass
class ElastNetMTAddonRuntime:
    enabled: bool = False
    workspace: str = "elastnetmt"
    model_kind: str = "gnm"
    cutoff: str = "12 angstroms"
    selection: str = 'atom_name=="CA"'
    active_mode_index: int = 0
    visible_overlays: list[str] = field(default_factory=list)
    overlay_parameters: dict[str, dict[str, Any]] = field(default_factory=dict)
    last_context_action: dict[str, Any] | None = None
    event_log: list[dict[str, Any]] = field(default_factory=list)
    cached_models: dict[str, Any] = field(default_factory=dict, repr=False)
    _cached_source: Any = field(default=None, repr=False)

    def snapshot(self) -> dict[str, Any]:
        # Molecular systems and dense model caches are runtime objects, not UI state.
        return {
            item.name: deepcopy(getattr(self, item.name))
            for item in fields(self)
            if item.name not in {"cached_models", "_cached_source"}
        }


def get_or_build_model(
    view: Any,
    model_type: Any,
    kind: str,
    *,
    molecular_system: Any | None = None,
    selection: str | None = None,
    structure_index: int = 0,
    cutoff: Any | None = None,
    syntax: str = "MolSysMT",
) -> Any:
    """Reuse an ENM only while its source and physical inputs remain unchanged.

    Default input is the viewer's public normalized ``molsys`` property.
    Explicit inputs may use any MolSysMT-supported form. Molecular conversion,
    selection and topology comparison belong to MolSysMT. Exact comparisons of
    ENM coordinates, periodic boxes and experimental B factors prevent a small
    displacement across a contact threshold from reusing an old spectrum.
    Source replacement or an edited cached input clears all models in this view.
    """
    import molsysmt as msm

    runtime = ensure_runtime(view)
    source = molecular_system if molecular_system is not None else view.molsys
    if source is not runtime._cached_source or source is None:
        runtime.cached_models.clear()
        runtime._cached_source = source
    if source is None:
        raise ValueError("A molecular system must be loaded in the view.")

    selection = runtime.selection if selection is None else selection
    cutoff = runtime.cutoff if cutoff is None else cutoff
    normalized = source
    if molecular_system is not None and msm.get_form(source) != "molsysmt.MolSys":
        normalized = msm.convert(source, to_form="molsysmt.MolSys")

    cache_key = f"{kind}:{selection}:{cutoff}:{structure_index}:{syntax}"
    model = runtime.cached_models.get(cache_key)
    try:
        if model is not None and not _model_matches_source(
            model, normalized, selection, structure_index, cutoff, syntax
        ):
            runtime.cached_models.clear()
            model = None
        if model is None:
            model = model_type(
                normalized,
                selection=selection,
                structure_index=structure_index,
                cutoff=cutoff,
                syntax=syntax,
            )
            runtime.cached_models[cache_key] = model
            record_event(
                view,
                "build_contact_model" if kind == "contacts" else f"build_{kind}_model",
                selection=selection,
                cutoff=str(cutoff),
                structure_index=structure_index,
            )
    except Exception:
        runtime.cached_models.clear()
        raise
    return model


def _model_matches_source(model, source, selection, structure_index, cutoff, syntax):
    import molsysmt as msm
    import numpy as np

    from elastnetmt import pyunitwizard as puw

    requested_cutoff = puw.parse.parse(cutoff) if isinstance(cutoff, str) else cutoff
    if not np.array_equal(
        puw.get_value(requested_cutoff, to_unit="nanometers"),
        puw.get_value(model.cutoff, to_unit="nanometers"),
    ):
        return False
    if not np.array_equal(
        msm.select(
            source,
            selection=selection,
            structure_indices=structure_index,
            syntax=syntax,
        ),
        model.atom_indices,
    ):
        return False
    # Compare the same one-frame molecular input that the model constructor uses.
    # MolSysMT owns extraction, including frame-associated experimental metadata.
    current_frame = msm.extract(source, structure_indices=structure_index)
    for attribute, unit in (
        ("coordinates", "nanometers"),
        ("box", "nanometers"),
        ("b_factor", "nanometers**2"),
    ):
        current = msm.get(current_frame, structure_indices=0, **{attribute: True})
        saved = msm.get(
            model.molecular_system, structure_indices=0, **{attribute: True}
        )
        if current is None or saved is None:
            if current is not saved:
                return False
        elif not np.array_equal(
            puw.get_value(current, to_unit=unit),
            puw.get_value(saved, to_unit=unit),
            equal_nan=True,
        ):
            return False
    return msm.compare(
        current_frame,
        model.molecular_system,
        attribute_type="topological",
        include_none=True,
    )


def ensure_runtime(view: Any) -> ElastNetMTAddonRuntime:
    runtime = getattr(view, "_elastnetmt_addon_runtime", None)
    if runtime is None:
        runtime = ElastNetMTAddonRuntime()
        setattr(view, "_elastnetmt_addon_runtime", runtime)
    return runtime


def record_event(view: Any, event: str, **payload: Any) -> ElastNetMTAddonRuntime:
    runtime = ensure_runtime(view)
    runtime.event_log.append({"event": event, **payload})
    return runtime


def set_overlay_visibility(
    runtime: ElastNetMTAddonRuntime, overlay_tag: str, visible: bool
) -> None:
    if visible:
        if overlay_tag not in runtime.visible_overlays:
            runtime.visible_overlays.append(overlay_tag)
    elif overlay_tag in runtime.visible_overlays:
        runtime.visible_overlays.remove(overlay_tag)


def update_overlay_parameters(
    runtime: ElastNetMTAddonRuntime, overlay_tag: str, **parameters: Any
) -> None:
    runtime.overlay_parameters[overlay_tag] = dict(parameters)
