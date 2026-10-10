"""Dense unit-spring matrices from validated node arrays and adjacency.

Inputs are finite distinct float64 positions (N, 3) in nanometers and a
symmetric boolean contact map (N, N) with a false diagonal. Model boundaries
own selection, units and validation. These operations do not select contacts,
diagonalize, change model state or impose connectivity. Outputs are new float64
arrays in node order: Kirchhoff (N, N), Hessian (3N, 3N), node-major XYZ blocks.
"""

import numpy as np


def build_kirchhoff(contacts):
    """Build a graph Laplacian; disconnected graphs are valid matrix inputs."""
    matrix = -contacts.astype(float)
    np.fill_diagonal(matrix, contacts.sum(axis=1))
    return matrix


def build_hessian(coords, contacts):
    """Build the ANM Hessian; spectral nullspace policy belongs to the model."""
    n = len(coords)
    hessian = np.zeros((3 * n, 3 * n), dtype=float)
    diffs = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    dist2 = np.sum(diffs**2, axis=2)
    outer_prods = np.einsum("ijk,ijg->ijkg", diffs, diffs)
    h_off_diag = np.zeros((n, n, 3, 3))
    idx_i, idx_j = np.where(contacts)
    if len(idx_i) > 0:
        h_off_diag[idx_i, idx_j] = (
            -outer_prods[idx_i, idx_j] / dist2[idx_i, idx_j, np.newaxis, np.newaxis]
        )
    for k in range(3):
        for g in range(3):
            hessian[k::3, g::3] = h_off_diag[:, :, k, g]
    h_diag_sum = -np.sum(h_off_diag, axis=1)
    for k in range(3):
        for g in range(3):
            hessian[k::3, g::3] += np.diag(h_diag_sum[:, k, g])
    return hessian
