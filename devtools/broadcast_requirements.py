"""Generate the owner's six ordinary environments; preserve reviewed recipes/pins."""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

import yaml
from dependency_sdk import ROOT, load_module
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

GROUPS = {
    "production": "production",
    "development": "development",
    "test": "test",
    "docs": "docs",
    "setup": "setup",
    "build": "conda-build",
}


def flatten(values: list) -> list[str]:
    """Read nested owner tooling groups without executing configuration."""
    if not isinstance(values, list):
        raise ValueError("Requirement groups must be lists")
    result = []
    for value in values:
        if isinstance(value, list):
            items = flatten(value)
        elif isinstance(value, str) and value.strip():
            items = [value]
        else:
            raise ValueError("Requirement groups need nonempty strings")
        for item in items:
            if item not in result:
                result.append(item)
    return result


def environment_documents(root: Path) -> dict[str, str]:
    """Metadata owns runtime; owner groups own tools and reviewed source selection."""
    contracts = load_module("dependency_constraints")
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    groups = yaml.safe_load((root / "devtools/requirements.yaml").read_text())
    routes = tomllib.loads((root / "devtools/dependency_routes.toml").read_text())
    source_ids = {item["id"]: item for item in routes["source_routes"]}
    runtime = {
        canonicalize_name(Requirement(value).name): value
        for value in project["dependencies"]
    }
    documents = {}
    for name, group in GROUPS.items():
        record = groups[group]
        if not isinstance(record, dict):
            raise ValueError(f"{group}: expected a mapping")
        channels = flatten(record["channels"])
        if channels != ["uibcdf", "conda-forge"]:
            raise ValueError("Ordinary environments require uibcdf then conda-forge")
        dependencies = [
            "python >=3.14,<3.15"
            if name == "development"
            else "python " + project["requires-python"]
        ]
        selected_runtime = dict(runtime) if name not in {"setup", "build"} else {}
        context_name = record.get("source_context")
        if context_name is not None:
            contexts = [
                item for item in routes["contexts"] if item["name"] == context_name
            ]
            if len(contexts) != 1:
                raise ValueError("Source context must name one reviewed selection")
            context = contexts[0]
            if context["environment"] != f"devtools/conda-envs/{name}_env.yaml":
                raise ValueError("Source context targets another environment")
            overlays = set(context.get("overlays", []))
            for identifier in context["sources"]:
                item = source_ids[identifier]
                source = canonicalize_name(item["name"])
                if item["role"] == "required-runtime" and source not in overlays:
                    selected_runtime.pop(source)
        tools = flatten(record["dependencies"])
        for tool in tools:
            parsed = contracts.conda_requirement(tool).requirement
            if canonicalize_name(parsed.name) in {"python", *runtime}:
                raise ValueError(
                    "Metadata/source context owns Python and runtime, not tooling groups"
                )
        dependencies += tools + list(selected_runtime.values())
        parsed = [contracts.conda_requirement(item) for item in dependencies]
        contracts.compare_requirements(
            parsed,
            ["python" + project["requires-python"], *selected_runtime.values()],
            allow_narrowing=True,
            narrowing_reason="Routine Python minor; fixed source replacements are separate",
        )
        documents[f"devtools/conda-envs/{name}_env.yaml"] = yaml.safe_dump(
            {"channels": channels, "dependencies": dependencies}, sort_keys=False
        )
    return documents


def generate(root: Path, *, check: bool = False) -> None:
    """Validate every output before writing; check mode never changes files."""
    documents = environment_documents(root)
    changed = [
        name
        for name, content in documents.items()
        if not (root / name).is_file() or (root / name).read_text() != content
    ]
    if check and changed:
        raise ValueError("Generated environments differ: " + ", ".join(changed))
    if not check:
        for name in changed:
            (root / name).write_text(documents[name])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        generate(args.root.resolve(), check=args.check)
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(f"Environment generation: FAIL — {exc}", file=sys.stderr)
        return 1
    print("Generated environment inputs: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
