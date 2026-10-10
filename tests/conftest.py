"""Local structures for reproducible scientific and integration checks."""

from importlib.resources import as_file, files

import pytest


@pytest.fixture(scope="session")
def reference_pdb():
    """Use MolSysMT's bundled 1TCD structure without network acquisition."""
    resource = files("molsysmt").joinpath("data/pdb/1tcd.pdb")
    with as_file(resource) as path:
        assert path.is_file(), "The installed MolSysMT must contain the 1TCD fixture"
        yield str(path)


@pytest.fixture
def network_pdb(tmp_path):
    """An irregular three-dimensional network with explicit experimental B factors."""
    coordinates = [
        (0, 0, 0),
        (3, 0, 0),
        (0, 4, 0),
        (0, 0, 5),
        (4, 4, 0),
        (4, 0, 5),
        (0, 4, 5),
        (8, 4, 3),
    ]
    lines = []
    for index, (x, y, z) in enumerate(coordinates, 1):
        lines.append(
            f"ATOM  {index:5d}  CA  ALA A{index:4d}    "
            f"{x:8.3f}{y:8.3f}{z:8.3f}{1.0:6.2f}{10 * index:6.2f}           C  \n"
        )
    path = tmp_path / "network.pdb"
    path.write_text("".join(lines) + "TER\nEND\n")
    return str(path)
