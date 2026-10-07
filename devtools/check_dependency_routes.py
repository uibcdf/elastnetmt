"""Invoke the fixed shared preflight without importing ElastNetMT science."""

from __future__ import annotations

import sys

from dependency_sdk import ROOT, load_module


def main() -> int:
    dependency_routes = load_module("dependency_routes")
    sys.argv[1:1] = ["--root", str(ROOT)]
    return dependency_routes.main()


if __name__ == "__main__":
    raise SystemExit(main())
