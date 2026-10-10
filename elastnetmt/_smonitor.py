# ElastNetMT SMonitor Configuration

from elastnetmt._private.smonitor.catalog import CODES as CODES
from elastnetmt._private.smonitor.catalog import SIGNALS as SIGNALS

PROFILE = "user"

SMONITOR = {
    "level": "WARNING",
    "trace_depth": 3,
    "capture_warnings": True,
    "capture_logging": True,
    "theme": "plain",
    "strict_config": False,
}
