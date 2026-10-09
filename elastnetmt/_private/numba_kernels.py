"""Numba kernels, loaded only at an explicitly selected parallel boundary."""

import numpy as np
from numba import njit, prange


@njit(parallel=True)
def build_kirchhoff(contacts, n_nodes):
    kirchhoff = -contacts.astype(np.float64)
    for i in prange(n_nodes):
        row_sum = 0.0
        for j in range(n_nodes):
            if i != j and contacts[i, j]:
                row_sum += 1.0
        kirchhoff[i, i] = row_sum
    return kirchhoff


@njit(parallel=True)
def build_hessian(coords, contacts, n_nodes):
    hessian = np.zeros((3 * n_nodes, 3 * n_nodes), dtype=np.float64)
    for i in prange(n_nodes):
        for j in range(n_nodes):
            if i == j:
                continue
            if contacts[i, j]:
                dx = coords[i, 0] - coords[j, 0]
                dy = coords[i, 1] - coords[j, 1]
                dz = coords[i, 2] - coords[j, 2]
                r2 = dx * dx + dy * dy + dz * dz
                h00 = -dx * dx / r2
                h01 = -dx * dy / r2
                h02 = -dx * dz / r2
                h11 = -dy * dy / r2
                h12 = -dy * dz / r2
                h22 = -dz * dz / r2
                hessian[3 * i, 3 * j] = h00
                hessian[3 * i, 3 * j + 1] = h01
                hessian[3 * i, 3 * j + 2] = h02
                hessian[3 * i + 1, 3 * j] = h01
                hessian[3 * i + 1, 3 * j + 1] = h11
                hessian[3 * i + 1, 3 * j + 2] = h12
                hessian[3 * i + 2, 3 * j] = h02
                hessian[3 * i + 2, 3 * j + 1] = h12
                hessian[3 * i + 2, 3 * j + 2] = h22
                hessian[3 * i, 3 * i] -= h00
                hessian[3 * i, 3 * i + 1] -= h01
                hessian[3 * i, 3 * i + 2] -= h02
                hessian[3 * i + 1, 3 * i] -= h01
                hessian[3 * i + 1, 3 * i + 1] -= h11
                hessian[3 * i + 1, 3 * i + 2] -= h12
                hessian[3 * i + 2, 3 * i] -= h02
                hessian[3 * i + 2, 3 * i + 1] -= h12
                hessian[3 * i + 2, 3 * i + 2] -= h22
    return hessian
