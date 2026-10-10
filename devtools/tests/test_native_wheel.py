"""Native distribution identity/resource failures must fail before admission."""

import tomllib
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from devtools import native_wheel
from devtools.native_wheel import inspect_wheel, verify_installed_wheel


def wheel(tmp_path, tag="cp311-abi3-linux_x86_64", omit=None, pure=False):
    path = tmp_path / f"elastnetmt-0.1.0-{tag}.whl"
    files = {
        "elastnetmt/__init__.py": b"__version__ = '0.1.0'",
        "elastnetmt/_rust.abi3.so": b"native-fixture",
        "elastnetmt-0.1.0.dist-info/WHEEL": f"Root-Is-Purelib: {str(pure).lower()}\n".encode(),
    }
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in files.items():
            if name != omit:
                archive.writestr(name, data)
    return path


INVENTORY = {"required_paths": ["site-packages/elastnetmt/__init__.py"]}


def test_native_wheel_records_exact_extension_and_runtime_bytes(tmp_path):
    evidence = inspect_wheel(wheel(tmp_path), INVENTORY)
    assert evidence["version"] == "0.1.0"
    assert len(evidence["wheel_sha256"]) == 64
    assert set(evidence["files"]) == {
        "elastnetmt/__init__.py",
        "elastnetmt/_rust.abi3.so",
    }


def test_native_wheel_rejects_retired_python2_module(tmp_path):
    path = wheel(tmp_path)
    with zipfile.ZipFile(path, "a") as archive:
        archive.writestr("elastnetmt/model/old_anm.py", b"print 'legacy'\n")
    with pytest.raises(ValueError, match="Retired Python 2"):
        inspect_wheel(path, INVENTORY)


def test_current_inventory_covers_runtime_and_all_python_compiles():
    root = Path(__file__).resolve().parents[2]
    owned = set()
    for package in ("elastnetmt", "molsysviewer_elastnetmt"):
        for path in (root / package).rglob("*"):
            if path.suffix == ".py" or path.name == "py.typed":
                owned.add("site-packages/" + path.relative_to(root).as_posix())
                if path.suffix == ".py":
                    compile(path.read_bytes(), str(path), "exec")
    inventory = tomllib.loads(
        (root / "devtools/conda-build/native_resources.toml").read_text()
    )
    assert set(inventory["required_paths"]) == owned
    assert "site-packages/elastnetmt/model/old_anm.py" not in owned
    assert (root / "devguide/legacy/old_anm.py.txt").is_file()


@pytest.mark.parametrize("tag", ["py3-none-any", "cp314-cp314-linux_x86_64"])
def test_native_wheel_rejects_pure_or_interpreter_specific_tag(tmp_path, tag):
    with pytest.raises(ValueError, match="cp311-abi3"):
        inspect_wheel(wheel(tmp_path, tag=tag), INVENTORY)


@pytest.mark.parametrize("omit", ["elastnetmt/__init__.py", "elastnetmt/_rust.abi3.so"])
def test_native_wheel_rejects_missing_runtime_or_extension(tmp_path, omit):
    with pytest.raises(ValueError):
        inspect_wheel(wheel(tmp_path, omit=omit), INVENTORY)


def test_native_wheel_rejects_purelib_metadata(tmp_path):
    with pytest.raises(ValueError, match="pure Python"):
        inspect_wheel(wheel(tmp_path, pure=True), INVENTORY)


def installed(tmp_path, monkeypatch):
    archive = wheel(tmp_path)
    root = tmp_path / "installed"
    with zipfile.ZipFile(archive) as payload:
        payload.extractall(root)
    package = SimpleNamespace(
        __file__=str(root / "elastnetmt/__init__.py"), __version__="0.1.0"
    )
    native = SimpleNamespace(
        __file__=str(root / "elastnetmt/_rust.abi3.so"), NUM_THREADS=1
    )
    monkeypatch.setattr(
        native_wheel.importlib,
        "import_module",
        lambda name: native if name.endswith("._rust") else package,
    )
    monkeypatch.setattr(
        native_wheel.importlib.metadata,
        "distribution",
        lambda name: SimpleNamespace(
            version="0.1.0", locate_file=lambda path: root / path
        ),
    )
    return archive, root


def test_exact_installed_hashes_pass(tmp_path, monkeypatch):
    archive, _ = installed(tmp_path, monkeypatch)
    assert (
        verify_installed_wheel(archive, INVENTORY, tmp_path / "checkout")["version"]
        == "0.1.0"
    )


@pytest.mark.parametrize("path", ["elastnetmt/__init__.py", "elastnetmt/_rust.abi3.so"])
def test_changed_installed_python_or_native_bytes_fail(tmp_path, monkeypatch, path):
    archive, root = installed(tmp_path, monkeypatch)
    (root / path).write_bytes(b"changed after science")
    with pytest.raises(ValueError, match="differs from wheel"):
        verify_installed_wheel(archive, INVENTORY, tmp_path / "checkout")


def test_source_import_cannot_qualify_installed_bytes(tmp_path, monkeypatch):
    archive, root = installed(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="outside the checkout"):
        verify_installed_wheel(archive, INVENTORY, root)


def test_other_native_import_cannot_qualify_wheel_bytes(tmp_path, monkeypatch):
    archive, root = installed(tmp_path, monkeypatch)
    native_wheel.importlib.import_module("elastnetmt._rust").__file__ = str(
        root / "elastnetmt/_rust.cpython-314.so"
    )
    with pytest.raises(ValueError, match="extension path"):
        verify_installed_wheel(archive, INVENTORY, tmp_path / "checkout")
