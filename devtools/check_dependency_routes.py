"""Invoke the fixed shared preflight without importing ElastNetMT science."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDK_SHA = "2d32048457c6d37093ae509f5626d00a5cda121b"
SDK = Path(os.environ.get("ELASTNETMT_SUITE_ROOT", ROOT / ".molsyssuite")).resolve()


def main() -> int:
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=SDK, text=True
    ).strip()
    if (
        head != SDK_SHA
        or subprocess.check_output(
            ["git", "status", "--porcelain", "--", "devtools"], cwd=SDK, text=True
        ).strip()
    ):
        raise RuntimeError("Use the accepted clean immutable dependency SDK")
    # Only this administrative process sees the isolated checker libraries.
    sys.path[:0] = [str(SDK), str(ROOT / ".molsyssuite-tools")]
    from devtools.scripts import dependency_routes

    if not Path(dependency_routes.__file__).resolve().is_relative_to(SDK):
        raise RuntimeError("Another editable SDK namespace was selected")
    sys.argv[1:1] = ["--root", str(ROOT)]
    return dependency_routes.main()


if __name__ == "__main__":
    raise SystemExit(main())
