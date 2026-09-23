import warnings
from typing import Type

from .elastnetmt_deprecation_warning import ElastNetMTDeprecationWarning
from .no_experimental_b_factors_warning import NoExperimentalBFactorsWarning
from .user_elastnetmt_warning import UserElastNetMTWarning

__all__ = [
    "UserElastNetMTWarning",
    "ElastNetMTDeprecationWarning",
    "NoExperimentalBFactorsWarning",
    "warn",
    "warn_once",
]


def warn(
    message_or_warning: str | Warning,
    category: Type[Warning] | None = None,
    *,
    stacklevel: int = 2,
) -> None:
    if isinstance(message_or_warning, Warning):
        warnings.warn(message_or_warning, stacklevel=stacklevel)
    else:
        warnings.warn(
            message_or_warning, category or UserElastNetMTWarning, stacklevel=stacklevel
        )


__WARNED_ONCE_CACHE__: set[tuple[Type[Warning], str]] = set()


def warn_once(
    message_or_warning: str | Warning,
    category: Type[Warning] | None = None,
    *,
    stacklevel: int = 2,
) -> None:
    if isinstance(message_or_warning, Warning):
        msg, cat = str(message_or_warning), type(message_or_warning)
    else:
        msg, cat = message_or_warning, category or UserElastNetMTWarning

    key = (cat, msg)
    if key in __WARNED_ONCE_CACHE__:
        return
    __WARNED_ONCE_CACHE__.add(key)
    warnings.warn(message_or_warning, cat, stacklevel=stacklevel)
