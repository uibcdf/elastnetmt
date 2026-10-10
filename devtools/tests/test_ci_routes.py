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
    matrices = [workflow["jobs"][f"test-{platform}"] for platform in ("linux", "macos")]
    for platform, matrix in zip(("linux", "macos"), matrices, strict=True):
        build_id = f"native-wheel-{platform}"
        assert set(matrix["needs"]) == {"nightly-decision", build_id}
        assert f"needs.{build_id}.result == 'success'" in matrix["if"]
        assert "always()" in matrix["if"]
        assert "needs.nightly-decision.result != 'success'" in matrix["if"]
        assert "inputs.probe_backlog != true" in matrix["if"]
        assert "continue-on-error" not in matrix
        build = workflow["jobs"][build_id]
        assert build["strategy"]["matrix"]["os"] == [
            "ubuntu-latest" if platform == "linux" else "macos-15"
        ]
        assert build["if"] == "inputs.probe_backlog != true"
        assert "continue-on-error" not in build
        assert {cell["os"] for cell in matrix["strategy"]["matrix"]["cfg"]} == set(
            build["strategy"]["matrix"]["os"]
        )
    assert matrices[0]["steps"] == matrices[1]["steps"]
    assert (
        workflow["jobs"]["native-wheel-linux"]["steps"]
        == workflow["jobs"]["native-wheel-macos"]["steps"]
    )
    cells = [
        cell for matrix in matrices for cell in matrix["strategy"]["matrix"]["cfg"]
    ]
    assert len(cells) == 8
    matrix = matrices[0]
    assert {(cell["os"], cell["python-version"]) for cell in cells} == {
        (os_name, version)
        for os_name in ("ubuntu-latest", "macos-15")
        for version in ("3.11", "3.12", "3.13", "3.14")
    }
    for cell in cells:
        expected = (
            f"test_env_py{cell['python-version'].replace('.', '')}.yaml"
            if cell["python-version"] in {"3.13", "3.14"}
            else "test_env.yaml"
        )
        assert cell["environment-file"] == f"devtools/conda-envs/{expected}"
    steps = {step.get("name"): step for step in matrix["steps"]}
    command = steps["Run tests"]["run"]
    assert (
        "python -m pytest --receptor=ci -v --cov-config=.coveragerc --cov=elastnetmt"
        in command
    )
    assert "unset PYTHONPATH" in command
    assert 'cd "$ENM_QUALIFICATION"' in command
    assert command.count("devtools/native_wheel.py") == 2
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
    assert "--receptor=ci" in addon["jobs"]["contract"]["steps"][-1]["run"]
    for filename in {cell["environment-file"] for cell in cells}:
        dependencies = yaml.safe_load((ROOT / filename).read_text())["dependencies"]
        assert "pytest-receptor=1.2.1" in dependencies

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
