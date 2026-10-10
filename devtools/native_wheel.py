"""Inspect ElastNetMT ABI3 wheels and verify their installed runtime bytes.

These component-owned checks do not install, execute tests or publish. They
qualify this package's resource/native contract; provider admission is separate.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import sys
import tomllib
import zipfile
from pathlib import Path, PurePosixPath

from packaging.utils import parse_wheel_filename


def inspect_wheel(wheel, inventory):
    """Return the hashes of required runtime files in one cp311 ABI3 wheel."""
    wheel = Path(wheel)
    name, version, _, tags = parse_wheel_filename(wheel.name)
    if name != "elastnetmt" or any(
        tag.interpreter != "cp311" or tag.abi != "abi3" or tag.platform == "any"
        for tag in tags
    ):
        raise ValueError("Expected a platform-specific ElastNetMT cp311-abi3 wheel")
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or any(
            PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
            for name in names
        ):
            raise ValueError("Ambiguous or unsafe wheel payload")
        required = [
            path.removeprefix("site-packages/") for path in inventory["required_paths"]
        ]
        extension = [
            path
            for path in names
            if path.startswith("elastnetmt/_rust.") and path.endswith((".so", ".pyd"))
        ]
        if len(extension) != 1 or ".abi3." not in extension[0]:
            raise ValueError("Wheel must contain exactly one ABI3 _rust extension")
        required += extension
        if any(path not in names for path in required):
            raise ValueError("Missing required runtime resource")
        wheel_metadata = archive.read(f"elastnetmt-{version}.dist-info/WHEEL").decode()
        if "Root-Is-Purelib: false" not in wheel_metadata:
            raise ValueError("Native wheel must not declare a pure Python payload")
        return {
            "version": str(version),
            "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
            "files": {
                path: hashlib.sha256(archive.read(path)).hexdigest()
                for path in required
            },
        }


def verify_installed_wheel(wheel, inventory, checkout):
    """Verify exact installed bytes outside checkout and load the native module.

    All owned runtime files must share the distribution installation root and
    match the inspected wheel, including the extension after scientific tests.
    """
    evidence = inspect_wheel(wheel, inventory)
    checkout = Path(checkout).resolve()
    distribution = importlib.metadata.distribution("elastnetmt")
    module = importlib.import_module("elastnetmt")
    root = Path(module.__file__).resolve().parent.parent
    if root.is_relative_to(checkout) or distribution.version != evidence["version"]:
        raise ValueError("Expected the exact installed wheel outside the checkout")
    for path, expected in evidence["files"].items():
        actual = root / path
        if (
            not actual.is_file()
            or not actual.resolve().is_relative_to(root)
            or Path(distribution.locate_file(path)).resolve() != actual.resolve()
            or hashlib.sha256(actual.read_bytes()).hexdigest() != expected
        ):
            raise ValueError(f"Installed resource differs from wheel: {path}")
    native = importlib.import_module("elastnetmt._rust")
    native_path = next(
        path for path in evidence["files"] if path.startswith("elastnetmt/_rust.")
    )
    if Path(native.__file__).resolve() != root / native_path:
        raise ValueError("Native import differs from the wheel's extension path")
    if module.__version__ != evidence["version"] or native.NUM_THREADS != 1:
        raise ValueError("Installed version or serial native contract differs")
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    args = parser.parse_args()
    inventory = tomllib.loads(args.inventory.read_text())
    evidence = verify_installed_wheel(args.wheel, inventory, args.checkout)
    print(json.dumps(evidence, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
