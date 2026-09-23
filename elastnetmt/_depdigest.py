# DepDigest configuration for ElastNetMT

LIBRARIES = {
    "numpy": {"type": "hard", "pypi": "numpy"},
    "pyunitwizard": {"type": "hard", "pypi": "pyunitwizard"},
    "molsysmt": {"type": "hard", "pypi": "molsysmt"},
    "tqdm": {"type": "hard", "pypi": "tqdm"},
    "scikit-learn": {"type": "soft", "pypi": "scikit-learn"},
    "lindelint": {"type": "soft", "pypi": "lindelint"},
    "nglview": {"type": "soft", "pypi": "nglview"},
    "matplotlib": {"type": "hard", "pypi": "matplotlib"},
    "cupy": {"type": "soft", "pypi": "cupy"},
}

MAPPING = {
    "Trajectory": "molsysmt",
    "MolecularSystem": "molsysmt",
    "Interpolator": "lindelint",
    "LinearRegression": "scikit-learn",
    "NGLWidget": "nglview",
    "cupy_array": "cupy",
}
