"""
ElastNetMT
A toolkit for Elastic Network Models in the MolSysSuite ecosystem.
"""

# Ruff E402 is intentional: configure SMonitor before importing models.
# ruff: noqa: E402

# versioningit
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("elastnetmt")
except PackageNotFoundError:
    # Package is not installed
    try:
        from ._version import __version__
    except ImportError:
        __version__ = "0.1.0"

# 1. SMonitor Configuration
from smonitor.integrations import ensure_configured as _ensure_smonitor_configured

from elastnetmt._private.smonitor import PACKAGE_ROOT as _SMONITOR_PACKAGE_ROOT

_ensure_smonitor_configured(_SMONITOR_PACKAGE_ROOT)

# 2. Units (PyUnitWizard)
# 5. Support ArgDigest and DepDigest
from argdigest import arg_digest
from depdigest import dep_digest

# 3. Expose Exceptions and Diagnostics
from ._private.smonitor import (
    ArgumentError as ArgumentError,
)
from ._private.smonitor import (
    ElastNetMTError as ElastNetMTError,
)
from ._private.smonitor import (
    ElastNetMTWarning as ElastNetMTWarning,
)
from ._private.smonitor import (
    InternalAlgorithmError as InternalAlgorithmError,
)
from ._private.smonitor import (
    LibraryNotFoundError as LibraryNotFoundError,
)
from ._private.smonitor import (
    warn as warn,
)
from ._pyunitwizard import puw as pyunitwizard

# 4. Import Core Models
from .model import (
    AnisotropicNetworkModel,
    ElasticNetworkModel,
    GaussianNetworkModel,
)

__all__ = [
    "pyunitwizard",
    "GaussianNetworkModel",
    "AnisotropicNetworkModel",
    "ElasticNetworkModel",
    "arg_digest",
    "dep_digest",
]
