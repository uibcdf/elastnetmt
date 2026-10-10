"""Native matrix contract gate; the bundled extension is required."""

import numpy as np
import pytest


@pytest.fixture(scope="module")
def native():
    # Required installed backend: a missing/broken extension is a failure.
    from elastnetmt import _rust

    return _rust


@pytest.fixture
def tetrahedron():
    return np.array(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.2, 0.3, 1.0]]
    ), ~np.eye(4, dtype=bool)


def test_native_independent_energy_and_six_rigid_modes(native, tetrahedron):
    coords, contacts = tetrahedron
    matrix = native.build_hessian(coords, contacts)
    u = np.random.default_rng(71).normal(size=coords.shape)
    energy = 0.0
    for i in range(len(coords)):
        for j in range(i):
            direction = coords[i] - coords[j]
            energy += (np.dot(u[i] - u[j], direction) / np.linalg.norm(direction)) ** 2
    np.testing.assert_allclose(u.ravel() @ matrix @ u.ravel(), energy, atol=1e-12)
    np.testing.assert_allclose(matrix, matrix.T, atol=1e-12)
    for axis in np.eye(3):
        for rigid in (np.tile(axis, (len(coords), 1)), np.cross(axis, coords)):
            np.testing.assert_allclose(matrix @ rigid.ravel(), 0, atol=1e-12)
    values = np.linalg.eigvalsh(matrix)
    np.testing.assert_allclose(values[:6], 0, atol=1e-12)
    assert np.all(values[6:] > 0)
    assert native.NUM_THREADS == 1


def test_native_rotation_scale_and_input_ownership(native, tetrahedron):
    coords, contacts = tetrahedron
    matrix = native.build_hessian(coords, contacts)
    q, _ = np.linalg.qr(np.random.default_rng(13).normal(size=(3, 3)))
    t = np.kron(np.eye(4), q.T)
    np.testing.assert_allclose(
        native.build_hessian(coords @ q + 2, contacts), t @ matrix @ t.T, atol=1e-12
    )
    np.testing.assert_allclose(
        native.build_hessian(coords * 10, contacts), matrix, atol=1e-12
    )
    np.testing.assert_array_equal(contacts, ~np.eye(4, dtype=bool))
    assert not np.shares_memory(matrix, coords)
    assert not np.shares_memory(matrix, contacts)


@pytest.mark.parametrize("order", ["C", "F", "strided"])
def test_native_matrix_parity_and_layout(native, tetrahedron, order):
    from elastnetmt._private.matrix_kernels import build_hessian, build_kirchhoff

    coords, contacts = tetrahedron
    if order == "strided":
        positions = np.zeros((4, 6))
        positions[:, ::2] = coords
        coords = positions[:, ::2]
        graph = np.zeros((8, 8), dtype=bool)
        graph[::2, ::2] = contacts
        contacts = graph[::2, ::2]
    else:
        coords, contacts = (
            np.array(coords, order=order),
            np.array(contacts, order=order),
        )
    np.testing.assert_allclose(
        native.build_hessian(coords, contacts),
        build_hessian(coords, contacts),
        atol=1e-12,
    )
    np.testing.assert_array_equal(
        native.build_kirchhoff(contacts), build_kirchhoff(contacts)
    )


def test_native_disconnected_and_empty_matrices(native):
    contacts = np.zeros((3, 3), dtype=bool)
    contacts[0, 1] = contacts[1, 0] = True
    expected = [[1.0, -1.0, 0.0], [-1.0, 1.0, 0.0], [0.0, 0.0, 0.0]]
    np.testing.assert_array_equal(native.build_kirchhoff(contacts), expected)
    h = native.build_hessian(np.eye(3), contacts)
    np.testing.assert_array_equal(h[6:, :], 0)
    assert native.build_kirchhoff(np.zeros((0, 0), dtype=bool)).shape == (0, 0)
    assert native.build_hessian(
        np.zeros((0, 3)), np.zeros((0, 0), dtype=bool)
    ).shape == (0, 0)


@pytest.mark.parametrize(
    "fault",
    ["shape", "asymmetric", "diagonal", "nan", "coordinate_shape", "coincident"],
)
def test_native_rejects_invalid_buffers(native, tetrahedron, fault):
    coords, contacts = tetrahedron
    if fault == "shape":
        contacts = contacts[:, :-1]
    elif fault == "asymmetric":
        contacts[0, 1] = False
    elif fault == "diagonal":
        contacts[0, 0] = True
    elif fault == "nan":
        coords[0, 0] = np.nan
    elif fault == "coordinate_shape":
        coords = coords[:, :2]
    elif fault == "coincident":
        coords[0] = coords[1]
    with pytest.raises(ValueError):
        native.build_hessian(coords, contacts)


def test_native_rejects_wrong_dtypes(native, tetrahedron):
    coords, contacts = tetrahedron
    with pytest.raises(TypeError):
        native.build_hessian(coords.astype(np.float32), contacts)
    with pytest.raises(TypeError):
        native.build_kirchhoff(contacts.astype(np.uint8))


def test_native_normalizes_numpy_boolean_bytes(native, tetrahedron):
    coords, contacts = tetrahedron
    # NumPy permits different nonzero bytes for True; Rust bool permits 0/1.
    raw = contacts.astype(np.uint8) * 255
    raw[np.triu(contacts)] = 2
    original = raw.copy()
    logical = raw.view(np.bool_)
    np.testing.assert_array_equal(
        native.build_kirchhoff(logical), native.build_kirchhoff(contacts)
    )
    np.testing.assert_allclose(
        native.build_hessian(coords, logical), native.build_hessian(coords, contacts)
    )
    np.testing.assert_array_equal(raw, original)
