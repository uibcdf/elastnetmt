from __future__ import annotations

from molsysviewer import (
    AddonContextActionSpec,
    AddonExportHelperSpec,
    AddonLifecycleSpec,
    AddonPanelSpec,
    AddonSectionSpec,
    AddonShapeProviderSpec,
    AddonSpec,
    AddonWorkspaceSpec,
)

from .adapters import (
    render_anisotropy_ellipsoids,
    render_contact_network,
    render_mode_vectors,
)
from .export import build_figure_export_payload as build_figure_export_payload
from .runtime import ensure_runtime, record_event
from .runtime import set_overlay_visibility as set_overlay_visibility
from .workbench import (
    get_modes_section as get_modes_section,
)
from .workbench import (
    get_network_overlays_section as get_network_overlays_section,
)
from .workbench import (
    get_runtime_snapshot as get_runtime_snapshot,
)

addon = AddonSpec(
    name="elastnetmt",
    package="elastnetmt",
    description="Elastic network analysis workspace for MolSysViewer.",
    workspaces=(
        AddonWorkspaceSpec(
            id="elastnetmt",
            title="Elastic Networks",
            entry_panel="modes",
            description="Workspace for GNM/ANM models and overlays.",
            order=40,
        ),
    ),
    panels=(
        AddonPanelSpec(
            id="model",
            title="Model",
            entry="molsysviewer_elastnetmt.panels.model",
            description="Model parameters and node selection.",
            order=10,
            widget_class="molsysviewer_elastnetmt.panels.model.ElastNetMTModelPanel",
        ),
        AddonPanelSpec(
            id="modes",
            title="Modes",
            entry="molsysviewer_elastnetmt.panels.modes",
            description="Normal mode selection and activation.",
            order=20,
            widget_class="molsysviewer_elastnetmt.panels.modes.ElastNetMTModesPanel",
        ),
        AddonPanelSpec(
            id="figures",
            title="Figures",
            entry="molsysviewer_elastnetmt.panels.figures",
            description="Export helpers and reproducible figure presets.",
            order=30,
            widget_class="molsysviewer_elastnetmt.panels.figures.ElastNetMTFiguresPanel",
        ),
    ),
    context_actions=(
        AddonContextActionSpec(
            id="show-contact-network",
            title="Show Contact Network",
            entry="molsysviewer_elastnetmt.context.show_contact_network",
            target_kinds=("structure",),
            group="elastnetmt",
            order=10,
        ),
        AddonContextActionSpec(
            id="show-mode-vectors",
            title="Show Mode Vectors",
            entry="molsysviewer_elastnetmt.context.show_mode_vectors",
            target_kinds=("structure",),
            group="elastnetmt",
            order=20,
        ),
        AddonContextActionSpec(
            id="show-anisotropy-ellipsoids",
            title="Show Anisotropy Ellipsoids",
            entry="molsysviewer_elastnetmt.context.show_anisotropy_ellipsoids",
            target_kinds=("structure",),
            group="elastnetmt",
            order=30,
        ),
    ),
    addon_sections=(
        AddonSectionSpec(
            id="modes",
            title="Modes",
            entry="molsysviewer_elastnetmt.workbench.modes",
            target_panel="addons",
            order=10,
        ),
        AddonSectionSpec(
            id="network-overlays",
            title="Network Overlays",
            entry="molsysviewer_elastnetmt.workbench.network_overlays",
            target_panel="addons",
            order=20,
        ),
    ),
    shape_providers=(
        AddonShapeProviderSpec(
            id="contact-links",
            title="Contact Links",
            entry="molsysviewer_elastnetmt.shapes.contact_links",
            kinds=("link", "network"),
            order=10,
        ),
        AddonShapeProviderSpec(
            id="anisotropy-ellipsoids",
            title="Anisotropy Ellipsoids",
            entry="molsysviewer_elastnetmt.shapes.anisotropy_ellipsoids",
            kinds=("ellipsoid", "anisotropy"),
            order=20,
        ),
    ),
    export_helpers=(
        AddonExportHelperSpec(
            id="enm-figure",
            title="ENM Figure Export",
            entry="molsysviewer_elastnetmt.export.figure",
            formats=("png", "html"),
            order=10,
        ),
    ),
    meta={
        "domain": "elastic_networks",
        "repo": "elastnetmt",
        "status": "skeleton",
    },
)


def on_enable(view):
    runtime = ensure_runtime(view)
    runtime.enabled = True
    record_event(view, "enable", workspace=runtime.workspace)


def on_disable(view):
    runtime = ensure_runtime(view)
    runtime.enabled = False
    record_event(view, "disable", workspace=runtime.workspace)


def on_context_action(view, action_id, payload):
    runtime = ensure_runtime(view)
    runtime.last_context_action = {"action_id": action_id, "payload": dict(payload)}

    if action_id == "show-contact-network":
        render_contact_network(view)
    elif action_id == "show-mode-vectors":
        render_mode_vectors(view, mode_index=runtime.active_mode_index)
    elif action_id == "show-anisotropy-ellipsoids":
        render_anisotropy_ellipsoids(view)

    record_event(view, "context_action", action_id=action_id)


lifecycle = AddonLifecycleSpec(
    on_enable=on_enable,
    on_disable=on_disable,
    on_context_action=on_context_action,
)


def get_addon():
    return addon
