"""Execute the published model docstrings against bundled local structures."""

import doctest
import importlib

import pytest


@pytest.mark.parametrize(
    "module",
    ["elastic_network_model", "gaussian_network_model", "anisotropic_network_model"],
)
def test_public_model_examples(module):
    owner = importlib.import_module(f"elastnetmt.model.{module}")
    result = doctest.testmod(owner, optionflags=doctest.ELLIPSIS)
    assert result.attempted > 0, "The model must provide a runnable public example"
    assert result.failed == 0, "Published example assertions must match the public API"
