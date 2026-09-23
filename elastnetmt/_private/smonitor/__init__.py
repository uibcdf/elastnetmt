from pathlib import Path

from smonitor.integrations.diagnostic import (
    CatalogException,
    CatalogWarning,
)

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent


class ElastNetMTError(CatalogException):
    """Base error for ElastNetMT."""

    pass


class ElastNetMTWarning(CatalogWarning):
    """Base warning for ElastNetMT."""

    pass


class ArgumentError(ElastNetMTError):
    """Error in function arguments."""

    pass


class InternalAlgorithmError(ElastNetMTError):
    """Error in internal calculation logic."""

    pass


class LibraryNotFoundError(ElastNetMTError):
    """Error when a required library is missing."""

    pass


def warn(message, code=None, **kwargs):
    import warnings

    warnings.warn(message, ElastNetMTWarning)
