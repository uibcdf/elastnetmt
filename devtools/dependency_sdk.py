"""Load only the accepted shared dependency operations for owner tools."""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDK_SHA = "c866f0aa85f5fa0aec91973421eb23080daefdcc"


def load_module(name: str):
    """Require an immutable clean SDK and verify the selected import origin."""
    sdk = Path(os.environ.get("ELASTNETMT_SUITE_ROOT", ROOT / ".molsyssuite")).resolve()
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=sdk, text=True
    ).strip()
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--", "devtools"], cwd=sdk, text=True
    ).strip()
    if head != SDK_SHA or dirty:
        raise ValueError("Use the accepted clean immutable dependency SDK")
    sys.path[:0] = [str(sdk), str(ROOT / ".molsyssuite-tools")]
    module = importlib.import_module("devtools.scripts." + name)
    if not Path(module.__file__).resolve().is_relative_to(sdk):
        raise ValueError("Another editable SDK namespace was selected")
    return module
