"""Protect viewer ENM cache inputs through actual public molecular operations."""

import json
from types import SimpleNamespace

import molsysmt as msm
import numpy as np
import pytest

from elastnetmt import pyunitwizard as puw
from molsysviewer_elastnetmt.adapters.contacts import get_or_build_contact_model
from molsysviewer_elastnetmt.adapters.modes import get_or_build_anm_model
from molsysviewer_elastnetmt.runtime import ensure_runtime


@pytest.fixture(params=[get_or_build_contact_model, get_or_build_anm_model])
def builder(request):
    return request.param


@pytest.fixture
def source(network_pdb):
    return msm.convert(network_pdb, to_form="molsysmt.MolSys")


def move_atom(source, displacement):
    coordinates = puw.get_value(msm.get(source, coordinates=True), to_unit="nm").copy()
    coordinates[0, -1, 0] += displacement
    msm.set(source, coordinates=puw.quantity(coordinates, "nm"))


def test_public_normalized_source_and_unchanged_reuse(builder, source):
    view = SimpleNamespace(molsys=source, molecular_system="unused.pdb", _molsys=None)
    before = msm.copy(source)
    first = builder(view)
    assert builder(view) is first
    assert msm.compare(
        source,
        before,
        atom_name=True,
        atom_id=True,
        group_name=True,
        group_id=True,
        bonded_atom_pairs=True,
        n_atoms=True,
    )
    np.testing.assert_array_equal(
        puw.get_value(msm.get(source, coordinates=True), to_unit="nm"),
        puw.get_value(msm.get(before, coordinates=True), to_unit="nm"),
    )
    assert len(ensure_runtime(view).event_log) == 1


def test_scene_replacement_invalidates_both_model_kinds(builder, source):
    viewer = pytest.importorskip("molsysviewer")
    view = viewer.MolSysView(debug_js=True)
    view.load(source)
    first = builder(view)
    replacement = msm.copy(source)
    move_atom(replacement, 2)
    view.load(replacement, mode="replace")
    second = builder(view)
    assert second is not first
    assert not np.array_equal(first.contacts, second.contacts)
    assert builder(view) is second


def test_explicit_input_overrides_view_and_invalidates_cache(builder, source):
    view = SimpleNamespace(molsys=source)
    first = builder(view)
    alternate = msm.copy(source)
    move_atom(alternate, 2)
    second = builder(view, molecular_system=alternate)
    assert second is not first
    assert not np.array_equal(first.contacts, second.contacts)
    assert builder(view, molecular_system=alternate) is second
    assert builder(view) is not second


def test_explicit_pdb_path_remains_supported(builder, source, network_pdb):
    view = SimpleNamespace(molsys=None)
    first = builder(view, molecular_system=network_pdb)
    assert first.n_nodes == 8
    assert builder(view, molecular_system=network_pdb) is first


def test_in_place_coordinate_edit_invalidates_even_below_allclose(builder, source):
    view = SimpleNamespace(molsys=source)
    first = builder(view)
    before = puw.get_value(msm.get(source, coordinates=True), to_unit="nm").copy()
    move_atom(source, 1e-8)
    after = puw.get_value(msm.get(source, coordinates=True), to_unit="nm")
    assert np.allclose(before, after)
    assert not np.array_equal(before, after)
    second = builder(view)
    assert second is not first
    assert builder(view) is second
    np.testing.assert_array_equal(
        puw.get_value(msm.get(second.molecular_system, coordinates=True), to_unit="nm"),
        after,
    )


def test_small_motion_across_cutoff_rebuilds_contact_graph(builder, source):
    coordinates = puw.get_value(msm.get(source, coordinates=True), to_unit="nm").copy()
    distance = np.linalg.norm(coordinates[0, -1] - coordinates[0, 0])
    moved = coordinates.copy()
    moved[0, -1, 0] += 1e-8
    moved_distance = np.linalg.norm(moved[0, -1] - moved[0, 0])
    cutoff = puw.quantity((distance + moved_distance) / 2, "nm")
    view = SimpleNamespace(molsys=source)
    first = builder(view, cutoff=cutoff)
    assert first.contacts[0, -1]
    msm.set(source, coordinates=puw.quantity(moved, "nm"))
    second = builder(view, cutoff=cutoff)
    assert second is not first
    assert not second.contacts[0, -1]


def test_mutated_model_cutoff_cannot_override_cached_request(builder, source):
    view = SimpleNamespace(molsys=source)
    first = builder(view)
    first.calculate_contacts(cutoff="0.5 nanometers")
    second = builder(view)
    assert second is not first
    assert puw.get_value(second.cutoff, to_unit="nm") == pytest.approx(1.2)


def test_in_place_topology_edit_invalidates_and_reselects_nodes(builder, source):
    view = SimpleNamespace(molsys=source)
    first = builder(view)
    msm.set(source, selection=[0], atom_name="CB")
    second = builder(view)
    assert second is not first
    assert second.n_nodes == first.n_nodes - 1
    assert 0 not in second.atom_indices


def test_nonselection_topology_and_b_factors_also_invalidate(builder, source):
    view = SimpleNamespace(molsys=source)
    first = builder(view)
    msm.set(source, selection=[0], group_name="GLY")
    second = builder(view)
    assert second is not first
    factors = msm.get(source, b_factor=True)
    values = puw.get_value(factors, to_unit="nm**2").copy()
    values.flat[0] += 1
    msm.set(source, b_factor=puw.quantity(values, "nm**2"))
    assert builder(view) is not second


def test_periodic_box_edit_invalidates_cached_contacts(builder, source):
    msm.set(source, box=puw.quantity(np.eye(3)[None] * 3, "nm"))
    view = SimpleNamespace(molsys=source)
    first = builder(view)
    msm.set(source, box=puw.quantity(np.eye(3)[None] * 4, "nm"))
    assert builder(view) is not first


def test_frame_choice_and_append_keep_valid_frame_models(builder, source):
    second = msm.copy(source)
    move_atom(second, 0.02)
    msm.append_structures(source, second)
    view = SimpleNamespace(molsys=source)
    first = builder(view, structure_index=0)
    alternate = builder(view, structure_index=1)
    assert alternate is not first
    assert builder(view, structure_index=0) is first
    assert builder(view, structure_index=1) is alternate
    move_atom(second, 2)
    msm.append_structures(source, second)
    appended = builder(view, structure_index=2)
    assert not np.array_equal(appended.contacts, first.contacts)
    retained = builder(view, structure_index=0)
    assert builder(view, structure_index=0) is retained
    np.testing.assert_array_equal(
        puw.get_value(
            msm.get(retained.molecular_system, coordinates=True), to_unit="nm"
        ),
        puw.get_value(
            msm.get(source, structure_indices=0, coordinates=True), to_unit="nm"
        ),
    )


def test_scene_addition_reselects_new_atoms(builder, source):
    viewer = pytest.importorskip("molsysviewer")
    view = viewer.MolSysView(debug_js=True)
    view.load(source)
    first = builder(view)
    addition = msm.copy(source)
    coordinates = puw.get_value(
        msm.get(addition, coordinates=True), to_unit="nm"
    ).copy()
    coordinates += 0.03
    msm.set(addition, coordinates=puw.quantity(coordinates, "nm"))
    view.load(addition, mode="add")
    second = builder(view)
    assert second is not first
    assert second.n_nodes == first.n_nodes * 2


def test_unloaded_view_discards_cache_and_refuses_old_model(builder, source):
    view = SimpleNamespace(molsys=source)
    builder(view)
    view.molsys = None
    with pytest.raises(ValueError, match="must be loaded"):
        builder(view)
    assert ensure_runtime(view).cached_models == {}


def test_runtime_snapshot_excludes_molecular_objects(source):
    view = SimpleNamespace(molsys=source)
    get_or_build_contact_model(view)
    from molsysviewer_elastnetmt.workbench import get_runtime_snapshot

    snapshot = get_runtime_snapshot(view)
    assert len(snapshot["cached_model_keys"]) == 1
    assert "cached_models" not in snapshot
    assert "_cached_source" not in snapshot
    json.dumps(snapshot)


@pytest.mark.parametrize("kind", ["gnm", "anm"])
def test_model_panel_uses_public_molsys(source, kind):
    from molsysviewer_elastnetmt.panels.model import ElastNetMTModelPanel

    view = SimpleNamespace(molsys=source, molecular_system="unused.pdb", _molsys=None)
    runtime = ensure_runtime(view)
    runtime.model_kind = kind
    assert ElastNetMTModelPanel()._run_compute(view, runtime) == 8
