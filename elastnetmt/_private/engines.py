"""Shared backend boundaries for ENM construction and spectral decomposition."""

from depdigest import dep_digest


def select_engine(engine):
    """Resolve auto to the bundled serial Rust constructor.

    Explicit engines retain their meaning. The required installed extension is
    imported only at construction; absence or load failure always propagates.
    """
    return "rust" if engine == "auto" else engine


def build_kirchhoff_rust(contacts):
    """Construct a new float64 Laplacian from validated bool contacts."""
    from elastnetmt import _rust

    return _rust.build_kirchhoff(contacts)


def build_hessian_rust(coords, contacts):
    """Construct a new float64 Hessian from numeric nm coordinates/contacts."""
    from elastnetmt import _rust

    return _rust.build_hessian(coords, contacts)


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
