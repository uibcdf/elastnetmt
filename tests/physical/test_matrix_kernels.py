"""Matrix-tool contracts from independent graph and central-spring definitions."""

import numpy as np
import pytest

from elastnetmt._private.matrix_kernels import build_hessian, build_kirchhoff


@pytest.fixture
def tetrahedron():
    coords = np.array(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.2, 0.3, 1.0]]
    )
    contacts = ~np.eye(4, dtype=bool)
    return coords, contacts


def test_laplacian_chain_and_disconnected_node():
    graph = np.zeros((4, 4), dtype=bool)
    graph[0, 1] = graph[1, 0] = graph[1, 2] = graph[2, 1] = True
    expected = [
        [1.0, -1.0, 0.0, 0.0],
        [-1.0, 2.0, -1.0, 0.0],
        [0.0, -1.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
    ]
    np.testing.assert_array_equal(build_kirchhoff(graph), expected)


def test_hessian_quadratic_energy_and_rigid_nullspace(tetrahedron):
    coords, contacts = tetrahedron
    matrix = build_hessian(coords, contacts)
    u = np.random.default_rng(7).normal(size=coords.shape)
    energy = 0.0
    for i in range(len(coords)):
        for j in range(i):
            if contacts[i, j]:
                direction = coords[i] - coords[j]
                direction /= np.linalg.norm(direction)
                energy += np.dot(u[i] - u[j], direction) ** 2
    np.testing.assert_allclose(u.ravel() @ matrix @ u.ravel(), energy, atol=1e-12)
    for axis in np.eye(3):
        for rigid in (np.tile(axis, (len(coords), 1)), np.cross(axis, coords)):
            np.testing.assert_allclose(matrix @ rigid.ravel(), 0, atol=1e-12)
    values = np.linalg.eigvalsh(matrix)
    np.testing.assert_allclose(values[:6], 0, atol=1e-12)
    assert np.all(values[6:] > 0)


def test_hessian_rotation_translation_and_length_scale(tetrahedron):
    coords, contacts = tetrahedron
    matrix = build_hessian(coords, contacts)
    q, _ = np.linalg.qr(np.random.default_rng(11).normal(size=(3, 3)))
    transform = np.kron(np.eye(len(coords)), q.T)
    rotated = build_hessian(coords @ q + [2, -3, 4], contacts)
    np.testing.assert_allclose(rotated, transform @ matrix @ transform.T, atol=1e-12)
    np.testing.assert_allclose(build_hessian(coords * 10, contacts), matrix, atol=1e-12)


def test_matrix_tools_do_not_mutate_or_alias_inputs(tetrahedron):
    coords, contacts = tetrahedron
    positions, graph = coords.copy(), contacts.copy()
    for out in (build_hessian(coords, contacts), build_kirchhoff(contacts)):
        assert out.dtype == np.float64
        assert not np.shares_memory(out, coords)
        assert not np.shares_memory(out, contacts)
    np.testing.assert_array_equal(coords, positions)
    np.testing.assert_array_equal(contacts, graph)
