"""Shared backend boundaries for ENM construction and spectral decomposition."""

from depdigest import dep_digest, is_installed


def select_engine(engine):
    """Resolve auto to Numba when discoverable, otherwise NumPy.

    Explicit selections are never replaced. Errors inside a discoverable backend
    propagate rather than being interpreted as its absence.
    """
    return (
        "parallel"
        if engine == "auto" and is_installed("numba")
        else ("vectorized" if engine == "auto" else engine)
    )


@dep_digest("numba")
def build_kirchhoff_parallel(contacts, n_nodes):
    from .numba_kernels import build_kirchhoff

    return build_kirchhoff(contacts, n_nodes)


@dep_digest("numba")
def build_hessian_parallel(coords, contacts, n_nodes):
    from .numba_kernels import build_hessian

    return build_hessian(coords, contacts, n_nodes)


@dep_digest("cupy")
def diagonalize_gpu(matrix):
    import cupy as cp

    eigenvalues, eigenvectors = cp.linalg.eigh(cp.asarray(matrix))
    return cp.asnumpy(eigenvalues), cp.asnumpy(eigenvectors)
