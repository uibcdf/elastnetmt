#!/usr/bin/env bash
set -euo pipefail
# A declared example is useful for review, but cannot produce release bytes.
if [[ "$PKG_VERSION" == "0.0.0" ]]; then
    echo "Select and review a real native release plan before building." >&2
    exit 1
fi
if [[ "$(rustc --version | cut -d ' ' -f 2)" != "1.98.1" ]]; then
    echo "Native build requires the reviewed Rust 1.98.1 toolchain." >&2
    exit 1
fi
export PYO3_PYTHON="$PYTHON"
actual_version=$("$PYTHON" -m versioningit)
if [[ "$actual_version" != "$PKG_VERSION" ]]; then
    echo "Source version $actual_version differs from Conda version $PKG_VERSION." >&2
    exit 1
fi
"$PYTHON" -m pip install --no-deps --no-build-isolation .
