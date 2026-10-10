# DepDigest configuration for ElastNetMT

LIBRARIES = {
    "numpy": {"type": "hard", "pypi": "numpy"},
    "pyunitwizard": {"type": "hard", "pypi": "pyunitwizard"},
    "molsysmt": {"type": "hard", "pypi": "molsysmt"},
    "tqdm": {"type": "hard", "pypi": "tqdm"},
    "sklearn": {"type": "soft", "pypi": "scikit-learn", "conda": "scikit-learn"},
    "lindelint": {"type": "soft", "pypi": "lindelint"},
    "nglview": {"type": "soft", "pypi": "nglview"},
    "matplotlib": {"type": "hard", "pypi": "matplotlib"},
    "cupy": {"type": "soft", "pypi": "cupy"},
    "numba": {"type": "soft", "pypi": "numba", "conda": "numba"},
}

MAPPING = {
    "Trajectory": "molsysmt",
    "MolecularSystem": "molsysmt",
    "Interpolator": "lindelint",
    "LinearRegression": "sklearn",
    "NGLWidget": "nglview",
    "cupy_array": "cupy",
}
