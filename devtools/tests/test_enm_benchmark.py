"""Exercise process isolation, measurement fields and requested-engine failures."""

import subprocess

import pytest

from devtools.enm_benchmark import load_prototype, run_case


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
