"""Absence and transitive failures must preserve explicit backend selection."""

import os
import subprocess
import sys

import pytest

from elastnetmt import GaussianNetworkModel
from elastnetmt._private import engines


def test_import_does_not_load_optional_engines():
    code = """
import molsysmt, pyunitwizard
import sys
before = set(sys.modules)
import elastnetmt
added = set(sys.modules) - before
assert not any(n == 'numba' or n.startswith('numba.') or n == 'cupy' or n.startswith('cupy.') for n in added), added
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_auto_uses_bundled_rust_without_loading_numba(network_pdb):
    model = GaussianNetworkModel(network_pdb)
    model.get_eigenvalues()
    assert model.engine_used == "rust"
    assert engines.select_engine("vectorized") == "vectorized"


@pytest.mark.parametrize("engine, dependency", [("parallel", "numba"), ("gpu", "cupy")])
def test_requested_missing_engine_is_not_replaced(
    network_pdb, monkeypatch, engine, dependency
):
    from depdigest.core import checker

    real_is_installed = checker.is_installed
    monkeypatch.setattr(
        checker,
        "is_installed",
        lambda name: False if name == dependency else real_is_installed(name),
    )
    model = GaussianNetworkModel(network_pdb, engine=engine)
    with pytest.raises(ImportError, match=dependency):
        model.get_eigenvalues()
    assert model._eigenvalues is None


def test_transitive_backend_failure_is_not_an_absence_fallback(
    network_pdb, monkeypatch
):
    def broken(*args):
        raise ImportError("broken native backend dependency")

    monkeypatch.setattr(
        "elastnetmt.model.gaussian_network_model.build_kirchhoff_rust", broken
    )
    model = GaussianNetworkModel(network_pdb)
    with pytest.raises(ImportError, match="broken native"):
        model.get_eigenvalues()
    assert model._eigenvalues is None
    assert model.kirchhoff_matrix is None
    assert model.engine_used is None
