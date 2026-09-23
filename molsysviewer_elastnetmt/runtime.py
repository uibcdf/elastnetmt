from __future__ import annotations

from dataclasses import asdict, dataclass, field
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

    def snapshot(self) -> dict[str, Any]:
        return asdict(self)


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
