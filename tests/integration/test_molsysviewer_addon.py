import importlib
import pathlib
import sys

import molsysmt as msm
import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))


def test_molsysviewer_elastnetmt_module_exposes_valid_addon_contract():
    molsysviewer = pytest.importorskip("molsysviewer")
    module = importlib.import_module("molsysviewer_elastnetmt")

    assert isinstance(module.addon, molsysviewer.AddonSpec)
    assert module.addon.name == "elastnetmt"
    assert [item.id for item in module.addon.workspaces] == ["elastnetmt"]
    assert [item.id for item in module.addon.panels] == ["model", "modes", "figures"]
    model_panel = next(p for p in module.addon.panels if p.id == "model")
    assert (
        model_panel.widget_class
        == "molsysviewer_elastnetmt.panels.model.ElastNetMTModelPanel"
    )
    assert [item.id for item in module.addon.context_actions] == [
        "show-contact-network",
        "show-mode-vectors",
        "show-anisotropy-ellipsoids",
    ]
    assert [item.id for item in module.addon.workbench_sections] == [
        "modes",
        "network-overlays",
    ]
    assert [item.id for item in module.addon.export_helpers] == ["enm-figure"]
    assert [item.id for item in module.addon.shape_providers] == [
        "contact-links",
        "anisotropy-ellipsoids",
    ]
    assert module.lifecycle.info() == {
        "has_on_enable": True,
        "has_on_disable": True,
        "has_on_context_action": True,
        "has_on_active_selection_changed": False,
    }


def test_molsysviewer_elastnetmt_lifecycle_initializes_runtime_and_tracks_actions():
    molsysviewer = pytest.importorskip("molsysviewer")
    module = importlib.import_module("molsysviewer_elastnetmt")
    view = molsysviewer.MolSysView(debug_js=True)

    module.on_enable(view)
    runtime = view._elastnetmt_addon_runtime

    assert runtime.enabled is True
    assert runtime.workspace == "elastnetmt"
    assert runtime.visible_overlays == []
    assert runtime.event_log[-1]["event"] == "enable"

    view.load("pdb_id:1tcd")
    module.on_context_action(
        view,
        "show-contact-network",
        {"addon": "elastnetmt", "addon_action_id": "show-contact-network"},
    )
    assert "elastnetmt:contacts" in runtime.visible_overlays
    assert runtime.last_context_action["action_id"] == "show-contact-network"
    assert any(
        message.get("op") == "add_network_links" for message in view._shape_history
    )

    module.on_context_action(
        view,
        "show-mode-vectors",
        {"addon": "elastnetmt", "addon_action_id": "show-mode-vectors"},
    )
    assert "elastnetmt:mode:0" in runtime.visible_overlays
    assert any(
        message.get("op") == "add_displacement_vectors"
        for message in view._shape_history
    )
    assert runtime.event_log[-1]["event"] == "context_action"

    module.on_disable(view)
    assert runtime.enabled is False
    assert runtime.event_log[-1]["event"] == "disable"


def test_molsysviewer_elastnetmt_contact_adapter_builds_atom_pairs_and_renders_links():
    pytest.importorskip("molsysviewer")
    adapter_module = importlib.import_module(
        "molsysviewer_elastnetmt.adapters.contacts"
    )
    molsysviewer_module = importlib.import_module("molsysviewer")

    molecular_system = msm.convert("pdb_id:1tcd", to_form="molsysmt.MolSys")
    view = molsysviewer_module.MolSysView(debug_js=True)
    view.load(molecular_system)

    layer, model = adapter_module.render_contact_network(
        view, molecular_system=molecular_system
    )
    atom_pairs = adapter_module.build_contact_atom_pairs(model)

    assert layer.tag == "elastnetmt:contacts"
    assert model.n_nodes > 0
    assert len(atom_pairs) > 0
    assert all(len(pair) == 2 for pair in atom_pairs)
    assert view._shape_history[-1]["op"] == "add_network_links"
    assert view._shape_history[-1]["options"]["tag"] == "elastnetmt:contacts"
    assert len(view._shape_history[-1]["options"]["atom_pairs"]) == len(atom_pairs)


def test_molsysviewer_elastnetmt_mode_adapter_builds_vectors_and_renders_displacements():
    pytest.importorskip("molsysviewer")
    adapter_module = importlib.import_module("molsysviewer_elastnetmt.adapters.modes")
    molsysviewer_module = importlib.import_module("molsysviewer")

    molecular_system = msm.convert("pdb_id:1tcd", to_form="molsysmt.MolSys")
    view = molsysviewer_module.MolSysView(debug_js=True)
    view.load(molecular_system)

    layer, model, vectors = adapter_module.render_mode_vectors(
        view, molecular_system=molecular_system, mode_index=0
    )

    assert layer.tag == "elastnetmt:mode:0"
    assert model.n_nodes > 0
    assert vectors.shape == (model.n_nodes, 3)
    assert view._shape_history[-1]["op"] == "add_displacement_vectors"
    assert view._shape_history[-1]["options"]["tag"] == "elastnetmt:mode:0"
    assert len(view._shape_history[-1]["options"]["atom_indices"]) == model.n_nodes
    assert len(view._shape_history[-1]["options"]["vectors"]) == model.n_nodes


def test_molsysviewer_elastnetmt_mode_adapter_respects_active_mode_and_reuses_cached_model():
    pytest.importorskip("molsysviewer")
    module = importlib.import_module("molsysviewer_elastnetmt")
    adapter_module = importlib.import_module("molsysviewer_elastnetmt.adapters.modes")
    molsysviewer_module = importlib.import_module("molsysviewer")

    molecular_system = msm.convert("pdb_id:1tcd", to_form="molsysmt.MolSys")
    view = molsysviewer_module.MolSysView(debug_js=True)
    view.load(molecular_system)
    module.on_enable(view)

    runtime = view._elastnetmt_addon_runtime
    runtime.active_mode_index = 1

    layer1, model1, vectors1 = adapter_module.render_mode_vectors(
        view, molecular_system=molecular_system
    )
    layer2, model2, vectors2 = adapter_module.render_mode_vectors(
        view, molecular_system=molecular_system, mode_index=2
    )

    assert layer1.tag == "elastnetmt:mode:1"
    assert layer2.tag == "elastnetmt:mode:2"
    assert model1 is model2
    assert runtime.active_mode_index == 2
    assert vectors1.shape == vectors2.shape == (model1.n_nodes, 3)
    assert np.any(np.not_equal(vectors1, vectors2))


def test_molsysviewer_elastnetmt_anisotropy_adapter_builds_ellipsoids():
    pytest.importorskip("molsysviewer")
    adapter_module = importlib.import_module(
        "molsysviewer_elastnetmt.adapters.anisotropy"
    )
    molsysviewer_module = importlib.import_module("molsysviewer")

    molecular_system = msm.convert("pdb_id:1tcd", to_form="molsysmt.MolSys")
    view = molsysviewer_module.MolSysView(debug_js=True)
    view.load(molecular_system)

    layer, model, eigenvalues, eigenvectors = (
        adapter_module.render_anisotropy_ellipsoids(
            view,
            molecular_system=molecular_system,
            mode_count=10,
        )
    )

    assert layer.tag == "elastnetmt:anisotropy"
    assert model.n_nodes > 0
    assert len(eigenvalues) == model.n_nodes
    assert len(eigenvectors) == model.n_nodes
    assert len(eigenvalues[0]) == 3
    assert len(eigenvectors[0]) == 3
    assert len(eigenvectors[0][0]) == 3
    assert view._shape_history[-1]["op"] == "add_anisotropy_ellipsoids"
    assert view._shape_history[-1]["options"]["tag"] == "elastnetmt:anisotropy"
    assert len(view._shape_history[-1]["options"]["eigenvalues"]) == model.n_nodes


def test_molsysviewer_elastnetmt_workbench_and_export_helpers_report_reproducible_state():
    pytest.importorskip("molsysviewer")
    module = importlib.import_module("molsysviewer_elastnetmt")
    export_module = importlib.import_module("molsysviewer_elastnetmt.export")
    workbench_module = importlib.import_module("molsysviewer_elastnetmt.workbench")
    molsysviewer_module = importlib.import_module("molsysviewer")

    molecular_system = msm.convert("pdb_id:1tcd", to_form="molsysmt.MolSys")
    view = molsysviewer_module.MolSysView(debug_js=True)
    view.load(molecular_system)
    module.on_enable(view)

    module.on_context_action(
        view,
        "show-contact-network",
        {"addon": "elastnetmt", "addon_action_id": "show-contact-network"},
    )
    module.on_context_action(
        view,
        "show-mode-vectors",
        {"addon": "elastnetmt", "addon_action_id": "show-mode-vectors"},
    )
    module.on_context_action(
        view,
        "show-anisotropy-ellipsoids",
        {"addon": "elastnetmt", "addon_action_id": "show-anisotropy-ellipsoids"},
    )

    modes_section = workbench_module.get_modes_section(view)
    overlays_section = workbench_module.get_network_overlays_section(view)
    export_payload = export_module.build_figure_export_payload(view)

    assert modes_section["title"] == "Modes"
    assert modes_section["item_title"] == "Mode 0"
    assert "cutoff=12 angstroms" in modes_section["item_subtitle"]
    assert overlays_section["title"] == "Network Overlays"
    assert "elastnetmt:contacts" in overlays_section["item_title"]
    assert export_payload["title"] == "ElastNetMT Figure Export"
    assert export_payload["figure_recipe"]["active_mode_index"] == 0
    assert "elastnetmt:contacts" in export_payload["figure_recipe"]["visible_overlays"]
    assert (
        export_payload["figure_recipe"]["overlay_parameters"]["elastnetmt:anisotropy"][
            "kind"
        ]
        == "anisotropy-ellipsoids"
    )


def test_molsysviewer_elastnetmt_demo_bundle_builds_complete_mvp_state():
    pytest.importorskip("molsysviewer")
    demo_module = importlib.import_module("molsysviewer_elastnetmt.demo")

    bundle = demo_module.build_demo_bundle(
        "pdb_id:1tcd",
        mode_index=1,
        show_contact_network=True,
        show_mode_vectors=True,
        show_anisotropy_ellipsoids=True,
        debug_js=True,
    )

    view = bundle["view"]
    assert (
        "elastnetmt:contacts"
        in bundle["network_overlays_section"]["snapshot"]["visible_overlays"]
    )
    assert (
        "elastnetmt:mode:1"
        in bundle["network_overlays_section"]["snapshot"]["visible_overlays"]
    )
    assert (
        "elastnetmt:anisotropy"
        in bundle["network_overlays_section"]["snapshot"]["visible_overlays"]
    )
    assert bundle["modes_section"]["item_title"] == "Mode 1"
    assert bundle["export_payload"]["figure_recipe"]["active_mode_index"] == 1
    assert any(
        message.get("op") == "add_network_links" for message in view._shape_history
    )
    assert any(
        message.get("op") == "add_displacement_vectors"
        for message in view._shape_history
    )
    assert any(
        message.get("op") == "add_anisotropy_ellipsoids"
        for message in view._shape_history
    )


def test_elastnetmt_model_panel_widget_class_is_resolvable_via_view_addons_manager():
    molsysviewer = pytest.importorskip("molsysviewer")
    module = importlib.import_module("molsysviewer_elastnetmt")

    molsysviewer.addons.clear()
    molsysviewer.addons.register(module.get_addon())
    view = molsysviewer.MolSysView(debug_js=True)

    widget = view.addons.resolve_panel_widget("elastnetmt", "model")

    molsysviewer.addons.clear()
    assert widget is not None
    assert type(widget).__name__ == "ElastNetMTModelPanel"
    assert isinstance(widget, molsysviewer.AddonPanelWidget)


def test_elastnetmt_model_panel_on_mount_pushes_initial_state():
    molsysviewer = pytest.importorskip("molsysviewer")
    module = importlib.import_module("molsysviewer_elastnetmt")

    molsysviewer.addons.clear()
    molsysviewer.addons.register(module.get_addon())
    view = molsysviewer.MolSysView(debug_js=True)

    widget = view.addons.resolve_panel_widget("elastnetmt", "model")
    sent = []
    widget.send = lambda msg: sent.append(msg)

    widget.on_mount(view)
    molsysviewer.addons.clear()

    assert len(sent) == 1
    assert sent[0]["type"] == "state"
    state = sent[0]["state"]
    assert state["model_kind"] == "gnm"
    assert state["cutoff"] == "12 angstroms"
    assert state["status"] == "idle"


def test_elastnetmt_model_panel_set_model_kind_action_updates_runtime_and_pushes_state():
    molsysviewer = pytest.importorskip("molsysviewer")
    module = importlib.import_module("molsysviewer_elastnetmt")

    molsysviewer.addons.clear()
    molsysviewer.addons.register(module.get_addon())
    view = molsysviewer.MolSysView(debug_js=True)

    widget = view.addons.resolve_panel_widget("elastnetmt", "model")
    sent = []
    widget.send = lambda msg: sent.append(msg)

    widget.handle_action(view, "set_model_kind", {"model_kind": "anm"})
    molsysviewer.addons.clear()

    runtime = view._elastnetmt_addon_runtime
    assert runtime.model_kind == "anm"
    assert sent[-1]["state"]["model_kind"] == "anm"
    assert any(e["event"] == "panel_set_model_kind" for e in runtime.event_log)


def test_elastnetmt_model_panel_compute_action_builds_model_and_reports_n_nodes():
    molsysviewer = pytest.importorskip("molsysviewer")
    module = importlib.import_module("molsysviewer_elastnetmt")

    molecular_system = msm.convert("pdb_id:1tcd", to_form="molsysmt.MolSys")

    molsysviewer.addons.clear()
    molsysviewer.addons.register(module.get_addon())
    view = molsysviewer.MolSysView(debug_js=True)
    view.load(molecular_system)

    widget = view.addons.resolve_panel_widget("elastnetmt", "model")
    sent = []
    widget.send = lambda msg: sent.append(msg)

    widget.handle_action(view, "compute", {})
    molsysviewer.addons.clear()

    states = [m for m in sent if m.get("type") == "state"]
    assert states[0]["state"]["status"] == "computing"
    final = states[-1]["state"]
    assert final["status"] == "done"
    assert final["n_nodes"] > 0

    runtime = view._elastnetmt_addon_runtime
    assert any(e["event"] == "panel_compute" for e in runtime.event_log)


def test_elastnetmt_modes_panel_widget_class_is_registered():
    pytest.importorskip("molsysviewer")
    module = importlib.import_module("molsysviewer_elastnetmt")

    modes_panel = next(p for p in module.addon.panels if p.id == "modes")
    assert (
        modes_panel.widget_class
        == "molsysviewer_elastnetmt.panels.modes.ElastNetMTModesPanel"
    )


def test_elastnetmt_modes_panel_on_mount_pushes_initial_state():
    molsysviewer = pytest.importorskip("molsysviewer")
    module = importlib.import_module("molsysviewer_elastnetmt")

    molsysviewer.addons.clear()
    molsysviewer.addons.register(module.get_addon())
    view = molsysviewer.MolSysView(debug_js=True)

    widget = view.addons.resolve_panel_widget("elastnetmt", "modes")
    sent = []
    widget.send = lambda msg: sent.append(msg)

    widget.on_mount(view)
    molsysviewer.addons.clear()

    assert len(sent) == 1
    assert sent[0]["type"] == "state"
    state = sent[0]["state"]
    assert state["mode_index"] == 0
    assert state["status"] == "idle"
    assert state["n_modes"] is None  # no model computed yet


def test_elastnetmt_modes_panel_set_mode_index_action():
    molsysviewer = pytest.importorskip("molsysviewer")
    module = importlib.import_module("molsysviewer_elastnetmt")

    molsysviewer.addons.clear()
    molsysviewer.addons.register(module.get_addon())
    view = molsysviewer.MolSysView(debug_js=True)

    widget = view.addons.resolve_panel_widget("elastnetmt", "modes")
    sent = []
    widget.send = lambda msg: sent.append(msg)

    widget.handle_action(view, "set_mode_index", {"mode_index": 3})
    molsysviewer.addons.clear()

    runtime = view._elastnetmt_addon_runtime
    assert runtime.active_mode_index == 3
    assert sent[-1]["state"]["mode_index"] == 3
    assert any(e["event"] == "panel_set_mode_index" for e in runtime.event_log)


def test_elastnetmt_modes_panel_show_vectors_action_renders_and_reports_n_vectors():
    molsysviewer = pytest.importorskip("molsysviewer")
    module = importlib.import_module("molsysviewer_elastnetmt")

    molecular_system = msm.convert("pdb_id:1tcd", to_form="molsysmt.MolSys")

    molsysviewer.addons.clear()
    molsysviewer.addons.register(module.get_addon())
    view = molsysviewer.MolSysView(debug_js=True)
    view.load(molecular_system)

    widget = view.addons.resolve_panel_widget("elastnetmt", "modes")
    sent = []
    widget.send = lambda msg: sent.append(msg)

    widget.handle_action(view, "show_mode_vectors", {"mode_index": 1})
    molsysviewer.addons.clear()

    states = [m for m in sent if m.get("type") == "state"]
    assert states[0]["state"]["status"] == "rendering"
    final = states[-1]["state"]
    assert final["status"] == "done"

    runtime = view._elastnetmt_addon_runtime
    assert runtime.active_mode_index == 1
    assert any(e["event"] == "panel_show_mode_vectors" for e in runtime.event_log)
    assert any(
        msg.get("op") == "add_displacement_vectors" for msg in view._shape_history
    )


def test_elastnetmt_figures_panel_widget_class_is_registered():
    pytest.importorskip("molsysviewer")
    module = importlib.import_module("molsysviewer_elastnetmt")

    figures_panel = next(p for p in module.addon.panels if p.id == "figures")
    assert (
        figures_panel.widget_class
        == "molsysviewer_elastnetmt.panels.figures.ElastNetMTFiguresPanel"
    )


def test_elastnetmt_figures_panel_on_mount_pushes_initial_state():
    molsysviewer = pytest.importorskip("molsysviewer")
    module = importlib.import_module("molsysviewer_elastnetmt")

    molsysviewer.addons.clear()
    molsysviewer.addons.register(module.get_addon())
    view = molsysviewer.MolSysView(debug_js=True)

    widget = view.addons.resolve_panel_widget("elastnetmt", "figures")
    sent = []
    widget.send = lambda msg: sent.append(msg)

    widget.on_mount(view)
    molsysviewer.addons.clear()

    assert len(sent) == 1
    state = sent[0]["state"]
    assert state["active_preset"] == "structure_network"
    assert state["format"] == "png"
    assert state["overlays"] == []
    assert state["status"] == "idle"


def test_elastnetmt_figures_panel_set_preset_and_export_actions():
    molsysviewer = pytest.importorskip("molsysviewer")
    module = importlib.import_module("molsysviewer_elastnetmt")

    molecular_system = msm.convert("pdb_id:1tcd", to_form="molsysmt.MolSys")

    molsysviewer.addons.clear()
    molsysviewer.addons.register(module.get_addon())
    view = molsysviewer.MolSysView(debug_js=True)
    view.load(molecular_system)
    module.on_enable(view)
    module.on_context_action(view, "show-contact-network", {})
    module.on_context_action(view, "show-mode-vectors", {})

    widget = view.addons.resolve_panel_widget("elastnetmt", "figures")
    sent = []
    widget.send = lambda msg: sent.append(msg)

    widget.handle_action(view, "set_preset", {"preset": "structure_mode"})
    assert sent[-1]["state"]["active_preset"] == "structure_mode"

    sent.clear()
    widget.handle_action(view, "export", {"preset": "structure_mode", "format": "png"})
    molsysviewer.addons.clear()

    states = [m for m in sent if m.get("type") == "state"]
    assert states[0]["state"]["status"] == "exporting"
    assert states[-1]["state"]["status"] == "done"

    runtime = view._elastnetmt_addon_runtime
    assert any(e["event"] == "panel_export_figure" for e in runtime.event_log)
