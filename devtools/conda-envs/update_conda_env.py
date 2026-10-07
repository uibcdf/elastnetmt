"""Update the active Conda interpreter without widening its Python contract."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conda_environment import apply_environment


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("conda_file", type=Path)
    args = parser.parse_args()
    try:
        apply_environment(
            args.conda_file.resolve(),
            f"{sys.version_info.major}.{sys.version_info.minor}",
            prefix=Path(sys.prefix),
        )
    except (
        OSError,
        ValueError,
        KeyError,
        yaml.YAMLError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"Environment update: FAIL — {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
