"""Complete PR coverage and conditional recovery retain component test selection."""

import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_contributor_routes_and_complete_supported_matrix():
    workflow = yaml.load(
        (ROOT / ".github/workflows/CI.yaml").read_text(), Loader=yaml.BaseLoader
    )
    assert (
        workflow["on"]["workflow_dispatch"]["inputs"]["probe_backlog"]["type"]
        == "boolean"
    )
    assert "paths-ignore" not in workflow["on"]["pull_request"]
    assert "paths" not in workflow["on"]["pull_request"]
    schedules = workflow["on"]["schedule"]
    assert {"cron": "0 9 * * MON"} in schedules
    assert {"cron": "19 2 * * *", "timezone": "America/Mexico_City"} in schedules
    matrix = workflow["jobs"]["test"]
    assert matrix["needs"] == "nightly-decision"
    assert "always()" in matrix["if"]
    assert "needs.nightly-decision.result != 'success'" in matrix["if"]
    assert "inputs.probe_backlog != true" in matrix["if"]
    assert "continue-on-error" not in matrix
    assert {
        (cell["os"], cell["python-version"])
        for cell in matrix["strategy"]["matrix"]["cfg"]
    } == {
        (os_name, version)
        for os_name in ("ubuntu-latest", "macos-15")
        for version in ("3.11", "3.12", "3.13")
    }
    for cell in matrix["strategy"]["matrix"]["cfg"]:
        expected = (
            "test_env_py313.yaml"
            if cell["python-version"] == "3.13"
            else "test_env.yaml"
        )
        assert cell["environment-file"] == f"devtools/conda-envs/{expected}"
    steps = {step.get("name"): step for step in matrix["steps"]}
    command = steps["Run tests"]["run"]
    assert "pytest -v --cov-config=.coveragerc --cov=elastnetmt" in command
    assert "--noconftest" not in command
    assert "--ignore" not in command and "smoke" not in command
    assert "if" not in steps["Run tests"]
    assert "continue-on-error" not in steps["Run tests"]
    assert (
        'platform.machine() == "arm64"'
        in steps["Verify interpreter and macOS architecture"]["run"]
    )

    source_step = steps["Install MolSysMT source for Python 3.13"]
    assert source_step["if"] == "matrix.cfg.python-version == '3.13'"
    assert "molsysmt@3bcfaf4d50df6c84ebd14505790ed5221543e5de" in source_step["run"]
    addon = yaml.load(
        (ROOT / ".github/workflows/molsysviewer_contract.yaml").read_text(),
        Loader=yaml.BaseLoader,
    )
    assert "paths" not in addon["on"]["pull_request"]
    assert "paths-ignore" not in addon["on"]["pull_request"]
    assert "continue-on-error" not in addon["jobs"]["contract"]

    # The YAML dependency belongs only to the explicit administrative route.
    pytest_config = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"][
        "pytest"
    ]["ini_options"]
    assert pytest_config["testpaths"] == ["tests"]
    assert "devtools/tests" not in command
    assert "test_ci_routes.py" not in command
    governance = workflow["jobs"]["governance"]["steps"]
    admin_command = next(
        step["run"]
        for step in governance
        if step.get("name") == "Test CI recovery and contributor routes"
    )
    assert "devtools/tests/test_ci_routes.py" in admin_command
    assert "tests/test_ci_routes.py" not in admin_command.replace(
        "devtools/tests/test_ci_routes.py", ""
    )
