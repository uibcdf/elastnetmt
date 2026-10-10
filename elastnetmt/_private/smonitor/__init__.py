from pathlib import Path

from smonitor.integrations.diagnostic import (
    CatalogException,
    CatalogWarning,
)

from .catalog import CODES
from .meta import META

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent


def emit_catalog(code, *, source, **extra):
    """Emit an owned diagnostic through SMonitor's supported catalog boundary."""
    from smonitor.integrations import emit_from_catalog

    if code not in CODES:
        raise KeyError(code)
    return emit_from_catalog(
        {
            "code": code,
            "level": "ERROR" if "-E" in code else "WARNING",
            "source": source,
        },
        package_root=PACKAGE_ROOT,
        meta=META,
        extra=extra,
    )


class ElastNetMTError(CatalogException):
    """Base error for ElastNetMT."""

    pass


class ElastNetMTWarning(CatalogWarning):
    """Base warning for ElastNetMT."""

    pass


class ArgumentError(ElastNetMTError):
    """Error in function arguments."""

    def __init__(self, message=None, *, code="ENM-E001", **kwargs):
        super().__init__(message, code=code, **kwargs)


class InternalAlgorithmError(ElastNetMTError):
    """Error in internal calculation logic."""

    pass


class DegenerateNetworkError(InternalAlgorithmError):
    """The network has additional unconstrained motions."""

    def __init__(self, message=None, *, code="ENM-E020", **kwargs):
        super().__init__(message, code=code, **kwargs)


class InvalidSpectrumError(InternalAlgorithmError):
    """The numerical decomposition violates the ENM spectrum contract."""

    def __init__(self, message=None, *, code="ENM-E030", **kwargs):
        super().__init__(message, code=code, **kwargs)


class UndefinedCorrelationError(ArgumentError):
    """A constant profile cannot define Pearson correlation."""

    def __init__(self, message=None, *, code="ENM-E011", **kwargs):
        super().__init__(message, code=code, **kwargs)


class CutoffOptimizationError(InternalAlgorithmError):
    """No candidate has an admissible spectrum and defined correlation."""

    def __init__(self, message=None, *, code="ENM-E021", **kwargs):
        super().__init__(message, code=code, **kwargs)


class LibraryNotFoundError(ElastNetMTError):
    """Error when a required library is missing."""

    pass


def warn(message, code=None, **kwargs):
    import warnings

    warnings.warn(message, ElastNetMTWarning)
