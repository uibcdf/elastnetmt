"""Exercise process isolation, measurement fields and requested-engine failures."""

import subprocess

import pytest

from devtools.enm_benchmark import load_prototype, profile_call, run_case


def case(**changes):
    return dict(
        model="ANM",
        engine="numpy",
        nodes=8,
        cutoff_nm=1.4,
        seed=1729,
        threads=1,
        repeats=2,
        solve=True,
        **changes,
    )


def test_fresh_process_measurement_and_thread_limits():
    result = run_case(case())
    assert result["matrix_shape"] == [24, 24]
    assert result["matrix_bytes"] == 24 * 24 * 8
    assert len(result["warm_construction_s"]) == 2
    assert all(value > 0 for value in result["warm_construction_s"])
    assert result["first_construction_s"] > 0
    assert result["eigh_s"] > 0
    assert 0 <= result["contact_density"] <= 1
    assert all(pool["num_threads"] == 1 for pool in result["threadpools"])
    before = result["peak_rss_before_engine_bytes"]
    after = result["peak_rss_after_construction_bytes"]
    assert before is None or after >= before > 0


def test_requested_native_file_must_exist(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_prototype(tmp_path / "missing.so")
    requested = case()
    requested["engine"] = "rust"
    with pytest.raises(subprocess.CalledProcessError) as failure:
        run_case(requested, tmp_path / "missing.so")
    assert "FileNotFoundError" in failure.value.stderr


def test_unknown_engine_and_incomparable_threads_are_rejected():
    requested = case()
    requested["engine"] = "unknown"
    with pytest.raises(ValueError, match="Unsupported"):
        run_case(requested)
    requested.update(engine="rust", threads=2)
    with pytest.raises(ValueError, match="serial"):
        run_case(requested)


def test_native_loader_cannot_accept_a_python_substitute(tmp_path):
    substitute = tmp_path / "_enm_prototype.py"
    substitute.write_text("raise AssertionError('Python substitute executed')\n")
    with pytest.raises(ImportError):
        load_prototype(substitute)


@pytest.fixture
def tetrahedron(tmp_path):
    structure = tmp_path / "tetrahedron.pdb"
    positions = [(0, 0, 0), (3, 0, 0), (0, 4, 0), (0, 0, 5)]
    structure.write_text(
        "".join(
            f"ATOM  {i:5d}  CA  ALA A{i:4d}    {x:8.3f}{y:8.3f}{z:8.3f}{1.0:6.2f}{10.0:6.2f}           C  \n"
            for i, (x, y, z) in enumerate(positions, 1)
        )
        + "TER\nEND\n"
    )
    return structure


def test_public_model_measurement_preserves_cache_and_engine(tetrahedron):
    requested = case()
    requested.update(workload="public-model", structure=str(tetrahedron))
    result = run_case(requested)
    assert result["nodes"] == 4
    assert result["engine_used"] == "vectorized"
    assert (
        result["initialization_plus_first_query_s"]
        > result["first_query_s"]
        > result["eigh_s"]
        > 0
    )
    assert len(result["cached_query_s"]) == 2
    assert all(pool["num_threads"] == 1 for pool in result["threadpools"])


@pytest.mark.parametrize("profile", [False, True])
def test_preparation_reuses_public_input_without_changing_contacts(
    tetrahedron, profile
):
    requested = case()
    requested.update(
        workload="public-preparation",
        structure=str(tetrahedron),
        profile_preparation=profile,
    )
    result = run_case(requested)
    assert result["nodes"] == 4
    assert result["preparation_parity_checked"] is True
    assert result["first_initialization_s"] > 0
    for field in ("prepared_initialization_s", "repeated_file_initialization_s"):
        assert len(result[field]) == 2
        assert all(value > 0 for value in result[field])
    assert result["profiled_first_initialization"] is profile
    if profile:
        assert 0 < len(result["profile"]) <= 40
        assert all(row["calls"] >= row["primitive_calls"] for row in result["profile"])
    else:
        assert result["profile"] is None


def test_profiled_measurements_cannot_be_mixed_into_solve_workload():
    requested = case()
    requested["profile_preparation"] = True
    with pytest.raises(ValueError, match="public-preparation"):
        run_case(requested)


def test_profiling_propagates_scientific_exceptions():
    def failure():
        raise ValueError("calculation failed")

    with pytest.raises(ValueError, match="calculation failed"):
        profile_call(failure)
