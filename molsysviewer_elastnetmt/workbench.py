from __future__ import annotations

from typing import Any

from .runtime import ensure_runtime


def get_runtime_snapshot(view: Any) -> dict[str, Any]:
    runtime = ensure_runtime(view)
    snapshot = runtime.snapshot()
    snapshot["cached_model_keys"] = sorted(runtime.cached_models.keys())
    return snapshot


def get_modes_section(view: Any) -> dict[str, Any]:
    runtime = ensure_runtime(view)
    return {
        "key": "elastnetmt:modes",
        "title": "Modes",
        "item_title": f"Mode {runtime.active_mode_index}",
        "item_subtitle": (
            f"model={runtime.model_kind}, cutoff={runtime.cutoff}, "
            f"selection={runtime.selection}"
        ),
        "snapshot": get_runtime_snapshot(view),
    }


def get_network_overlays_section(view: Any) -> dict[str, Any]:
    runtime = ensure_runtime(view)
    return {
        "key": "elastnetmt:network-overlays",
        "title": "Network Overlays",
        "item_title": ", ".join(runtime.visible_overlays)
        if runtime.visible_overlays
        else "No overlays active",
        "item_subtitle": f"{len(runtime.visible_overlays)} active overlay(s)",
        "snapshot": get_runtime_snapshot(view),
    }
