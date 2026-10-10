"""Native producer preconditions fail before installation of release bytes."""

import os
import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_native_build_declares_one_floor_and_the_reviewed_toolchain():
    config = yaml.safe_load(
        (ROOT / "devtools/conda-build/conda_build_config.yaml").read_text()
    )
    assert config["python"] == ["3.11"]
    assert config["rust_compiler_version"] == ["1.98.1"]
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    extension = project["tool"]["setuptools-rust"]["ext-modules"][0]
    assert extension["py-limited-api"] == "cp311"
    assert extension["cargo-manifest-args"] == ["--locked"]


@pytest.mark.parametrize(
    ("version", "rust", "source_version", "error"),
    [
        ("0.0.0", "1.98.1", "0.0.0", "real native release plan"),
        ("0.1.0", "1.97.1", "0.1.0", "reviewed Rust"),
        ("0.2.0", "1.98.1", "0.1.0", "differs from Conda version"),
        ("0.1.0", "1.98.1", "0.1.0", None),
    ],
)
def test_build_rejects_example_wrong_toolchain_and_source_identity(
    tmp_path, version, rust, source_version, error
):
    # Instrument only the external tools; execute the actual producer script.
    # This validates the build boundary, not Conda archives or native science.
    python = tmp_path / "producer-python"
    python.write_text(
        "#!/bin/bash\nset -eu\n"
        'if [[ "$*" == "-m versioningit" ]]; then\n'
        f'  echo "{source_version}"\n'
        "else\n"
        '  printf "%s\\n" "$@" > "$ENM_INSTALL_CAPTURE"\n'
        "fi\n"
    )
    compiler = tmp_path / "rustc"
    compiler.write_text(f'#!/bin/bash\necho "rustc {rust} (producer fixture)"\n')
    python.chmod(0o755)
    compiler.chmod(0o755)
    capture = tmp_path / "installation.txt"
    result = subprocess.run(
        ["bash", str(ROOT / "devtools/conda-build/build.sh")],
        cwd=tmp_path,
        env={
            **os.environ,
            "PKG_VERSION": version,
            "PYTHON": str(python),
            "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"],
            "ENM_INSTALL_CAPTURE": str(capture),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    if error:
        assert result.returncode != 0
        assert error in result.stderr
        assert not capture.exists()
    else:
        assert result.returncode == 0, result.stderr
        assert capture.read_text().splitlines() == [
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--no-build-isolation",
            ".",
        ]
