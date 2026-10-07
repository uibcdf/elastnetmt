"""Validate and invoke this owner's Conda environment operations.

Python range semantics belong to the fixed shared dependency SDK. Environment
selection and the create/update command remain local development tooling.
"""

from __future__ import annotations

import copy
import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from dependency_sdk import ROOT, load_module


def selected_environment(path: Path, minor: str, *, root: Path = ROOT) -> dict:
    """Narrow metadata and existing YAML without widening either contract."""
    contracts = load_module("dependency_constraints")
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    selected = contracts.narrow_python(project["requires-python"], minor)[1]
    if path.name == "development_env.yaml" and minor != "3.14":
        raise ValueError("Routine development requires Python 3.14")
    routes = tomllib.loads((root / "devtools/dependency_routes.toml").read_text())
    relative = str(path.resolve().relative_to(root.resolve()))
    source_minors = {
        item["python_minor"]
        for item in routes["contexts"]
        if item["environment"] == relative and item.get("sources")
    }
    if source_minors and minor not in source_minors:
        raise ValueError("Selected Python does not match this fixed-source environment")
    document = yaml.safe_load(path.read_text())
    if not isinstance(document, dict):
        raise ValueError("Environment must be a mapping")
    dependencies = document.get("dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        raise ValueError("Environment needs a nonempty dependencies list")
    python = []
    for item in dependencies:
        if isinstance(item, str):
            requirement = contracts.conda_requirement(item)
            if requirement.requirement.name == "python":
                python.append(requirement)
        elif not (
            isinstance(item, dict)
            and set(item) == {"pip"}
            and isinstance(item["pip"], list)
            and all(isinstance(value, str) and value.strip() for value in item["pip"])
        ):
            raise ValueError("Invalid environment dependency entry")
    if len(python) > 1:
        raise ValueError("Environment must not repeat Python selectors")
    if python:
        if python[0].build:
            raise ValueError("Python build selection requires explicit review")
        # The whole requested minor must fit the existing selector, including
        # patch floors/ceilings. Do not replace a specialized range silently.
        contracts.compare_requirements(
            [contracts.conda_requirement(selected)],
            [str(python[0].requirement)],
            allow_narrowing=True,
            narrowing_reason="Explicit owner environment minor selection",
        )
    result = copy.deepcopy(document)
    result["dependencies"] = [selected] + [
        item
        for item in dependencies
        if not isinstance(item, str) or not re.match(r"^python(?:$|[ =<>!~])", item)
    ]
    # The operation targets its CLI name or active prefix, never a name/prefix
    # silently supplied by the input manifest.
    result.pop("name", None)
    result.pop("prefix", None)
    return result


def manager() -> str:
    """Respect explicit manager paths, allowing Mamba without Conda."""
    for variable, command in (("MAMBA_EXE", "mamba"), ("CONDA_EXE", "conda")):
        selected = os.environ.get(variable)
        if selected:
            resolved = shutil.which(selected)
            if not resolved:
                raise ValueError(f"{variable} does not identify an executable")
            return resolved
        resolved = shutil.which(command)
        if resolved:
            return resolved
    raise ValueError("Install Conda or Mamba before managing an environment")


def apply_environment(
    path: Path,
    minor: str,
    *,
    name: str | None = None,
    prefix: Path | None = None,
    root: Path = ROOT,
) -> None:
    """Validate first, use an argument vector, and propagate manager failures."""
    if (name is None) == (prefix is None):
        raise ValueError("Select exactly one new name or active prefix")
    if name is not None and not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.@-]*", name):
        raise ValueError("Invalid Conda environment name")
    if prefix is not None and not (prefix / "conda-meta").is_dir():
        raise ValueError("Update requires an active Conda prefix")
    content = selected_environment(path, minor, root=root)
    command = manager()
    with TemporaryDirectory(prefix="elastnetmt-environment-") as temporary:
        manifest = Path(temporary) / "environment.yaml"
        manifest.write_text(yaml.safe_dump(content, sort_keys=False))
        arguments = (
            ["create", "--name", name]
            if name is not None
            else ["update", "--prefix", str(prefix)]
        )
        arguments += ["--file", str(manifest)]
        if prefix is not None:
            arguments.append("--prune")
        subprocess.run(
            [command, "env", *arguments],
            check=True,
            env={**os.environ, "CONDA_CHANNEL_PRIORITY": "strict"},
        )
