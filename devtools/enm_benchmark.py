"""Fresh-process ENM matrix and public-model measurements; see ../rust/README.md.

Public operations: load_native(path), load_prototype(path), run_case(case, extension=None).
The CLI writes raw process samples, never a speed threshold or best-of result.
Scientific imports belong to workers, after thread environment configuration.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import math
import os
import platform
import subprocess
import sys
import tempfile
import time
from importlib.machinery import ExtensionFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_prototype(path):
    """Load the exact requested native file; absence/load errors propagate.

    This development-only adapter neither searches sys.path nor substitutes
    another engine. The private module initialization name is _enm_prototype.
    """
    return load_native(path, "_enm_prototype")


def load_native(path, module_name="_rust"):
    """Load exact native bytes with the production or historical init name."""
    if module_name not in {"_rust", "_enm_prototype"}:
        raise ValueError("Unknown native initialization name")
    path = Path(path).resolve(strict=True)
    loader = ExtensionFileLoader(module_name, str(path))
    spec = importlib.util.spec_from_file_location(module_name, path, loader=loader)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load the requested native extension: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def peak_rss_bytes():
    """Process-lifetime RSS high-water mark on Linux/macOS, None elsewhere."""
    if sys.platform not in ("linux", "darwin"):
        return None
    import resource

    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(peak if sys.platform == "darwin" else peak * 1024)


def measure(operation):
    """Return a result and wall seconds for that synchronous operation."""
    start = time.perf_counter()
    result = operation()
    return result, time.perf_counter() - start


def worker(case, extension):
    """Compute one input/engine case; called only in a fresh child interpreter."""
    if case.get("workload") == "public-model":
        return public_model_worker(case)
    start = time.perf_counter()
    import molsysmt as msm
    import numpy as np
    import pyunitwizard as puw
    from threadpoolctl import threadpool_info

    from elastnetmt._private import matrix_kernels

    import_s = time.perf_counter() - start
    n = case["nodes"]
    coords = np.random.default_rng(case["seed"]).uniform(
        0, (n / 10) ** (1 / 3), size=(n, 3)
    )
    contacts, contact_s = measure(
        lambda: msm.structure.get_contacts(
            puw.quantity(coords[np.newaxis], "nanometers"),
            threshold=f"{case['cutoff_nm']} nanometers",
            pbc=False,
            use_gpu=False,
            num_threads=case["threads"],
            parallel=case["threads"] > 1,
        )[0]
    )
    contacts = np.array(contacts, dtype=bool, order="C", copy=True)
    np.fill_diagonal(contacts, False)
    assert np.array_equal(contacts, contacts.T)
    before = peak_rss_bytes()
    engine = case["engine"]
    module, engine_import_s = measure(
        lambda: (
            load_native(extension, case.get("native_module", "_rust"))
            if engine == "rust"
            else (
                __import__(
                    "elastnetmt._private.numba_kernels", fromlist=["build_hessian"]
                )
                if engine == "numba"
                else matrix_kernels
            )
        )
    )
    if case["model"] == "GNM":
        operation = (
            (lambda: module.build_kirchhoff(contacts, n))
            if engine == "numba"
            else (lambda: module.build_kirchhoff(contacts))
        )
    else:
        operation = (
            (lambda: module.build_hessian(coords, contacts, n))
            if engine == "numba"
            else (lambda: module.build_hessian(coords, contacts))
        )
    matrix, first_s = measure(operation)
    shape, matrix_bytes = list(matrix.shape), matrix.nbytes
    del matrix
    warmed = []
    for _ in range(case["repeats"]):
        matrix, elapsed = measure(operation)
        warmed.append(elapsed)
        del matrix
    construction_peak = peak_rss_bytes()
    # Check parity after measuring construction memory: the NumPy oracle builds
    # large temporaries and must not contaminate the native phase's RSS mark.
    matrix = operation()
    reference = (
        matrix_kernels.build_kirchhoff(contacts)
        if case["model"] == "GNM"
        else matrix_kernels.build_hessian(coords, contacts)
    )
    np.testing.assert_allclose(matrix, reference, rtol=1e-12, atol=1e-12)
    del reference
    np.testing.assert_allclose(matrix, matrix.T, rtol=1e-12, atol=1e-12)
    solve_s = solve_peak = None
    if case["solve"]:
        (values, vectors), solve_s = measure(lambda: np.linalg.eigh(matrix))
        solve_peak = peak_rss_bytes()
        assert np.isfinite(values).all()
        residual = np.linalg.norm(matrix @ vectors - vectors * values)
        assert residual <= 1e-10 * max(1, np.linalg.norm(matrix))
    return {
        **case,
        "imports_s": import_s,
        "contacts_s": contact_s,
        "contact_density": float(contacts.sum() / max(1, n * (n - 1))),
        "engine_import_s": engine_import_s,
        "first_construction_s": first_s,
        "warm_construction_s": warmed,
        "matrix_shape": shape,
        "matrix_bytes": matrix_bytes,
        "peak_rss_before_engine_bytes": before,
        "peak_rss_after_construction_bytes": construction_peak,
        "eigh_s": solve_s,
        "peak_rss_after_eigh_and_parity_bytes": solve_peak,
        "numpy": np.__version__,
        "molsysmt": msm.__version__,
        "threadpools": threadpool_info(),
    }


def public_model_worker(case):
    """Measure actual public initialization, first query and cached queries.

    Use the runtime on the worker's import path, without injecting the checkout.
    NumPy eigh is timed transparently; caching must prevent repeated solves.
    Provider contacts retain the model's public defaults and are part of init.
    """
    start = time.perf_counter()
    import numpy as np
    from threadpoolctl import threadpool_info

    import elastnetmt as enm

    imports_s = time.perf_counter() - start
    model_type = (
        enm.GaussianNetworkModel
        if case["model"] == "GNM"
        else enm.AnisotropicNetworkModel
    )
    engine = {"numpy": "vectorized", "numba": "parallel", "rust": "rust"}[
        case["engine"]
    ]
    model, init_s = measure(
        lambda: model_type(
            case["structure"], cutoff=f"{case['cutoff_nm']} nm", engine=engine
        )
    )
    eig_times = []
    original = np.linalg.eigh

    def timed_eigh(matrix):
        result, elapsed = measure(lambda: original(matrix))
        eig_times.append(elapsed)
        return result

    np.linalg.eigh = timed_eigh
    try:
        modes, first_query_s = measure(model.get_modes)
        peak = peak_rss_bytes()
        assert np.isfinite(modes).all()
        cached = []
        for _ in range(case["repeats"]):
            result, elapsed = measure(model.get_modes)
            np.testing.assert_array_equal(result, modes)
            cached.append(elapsed)
        assert len(eig_times) == 1, "Cached queries must not diagonalize again"
    finally:
        np.linalg.eigh = original
    native = sys.modules.get("elastnetmt._rust")
    return {
        **case,
        "nodes": model.n_nodes,
        "runtime_file": enm.__file__,
        "engine_used": model.engine_used,
        "imports_s": imports_s,
        "initialization_s": init_s,
        "first_query_s": first_query_s,
        "initialization_plus_first_query_s": init_s + first_query_s,
        "cached_query_s": cached,
        "eigh_s": eig_times[0],
        "peak_rss_after_query_bytes": peak,
        "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest()
        if native
        else None,
        "numpy": np.__version__,
        "threadpools": threadpool_info(),
    }


def run_case(case, extension=None):
    """Run one case in a fresh process with explicit native/JIT thread limits.

    Matrix cases contain model (GNM/ANM), engine (numpy/numba/rust), nodes,
    cutoff_nm, seed, threads, repeats and solve. For workload='public-model',
    structure supplies a molecular file and node count comes from its selection;
    the bundled runtime engine is used. Timings exclude process startup.
    Missing/failed engines and failed numerical checks raise; no fallback.
    Temporary worker files/caches are removed on success and failure.
    """
    if case.get("workload", "matrices") not in {"matrices", "public-model"}:
        raise ValueError("Unsupported workload")
    if case.get("workload") == "public-model" and extension is not None:
        raise ValueError("Public models use their bundled extension")
    if case["engine"] not in {"numpy", "numba", "rust"} or case["model"] not in {
        "GNM",
        "ANM",
    }:
        raise ValueError("Unsupported model or engine")
    count_keys = (
        ("threads", "repeats")
        if case.get("workload") == "public-model"
        else ("nodes", "threads", "repeats")
    )
    if any(case[key] < 1 for key in count_keys):
        raise ValueError("nodes, threads and repeats must be positive")
    if not math.isfinite(case["cutoff_nm"]) or case["cutoff_nm"] <= 0:
        raise ValueError("cutoff_nm must be finite and positive")
    if case["engine"] == "rust" and case["threads"] != 1:
        raise ValueError("The Rust serial constructor requires threads=1")
    with tempfile.TemporaryDirectory(prefix="elastnetmt-enm-benchmark-") as work:
        result_path = Path(work) / "result.json"
        env = dict(os.environ)
        for name in (
            "MKL_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "OMP_NUM_THREADS",
            "NUMBA_NUM_THREADS",
        ):
            env[name] = str(case["threads"])
        env.update(PYTHONDONTWRITEBYTECODE="1", NUMBA_CACHE_DIR=work)
        subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--worker",
                json.dumps(case),
                str(result_path),
                str(extension or ""),
            ],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )
        return json.loads(result_path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[64, 256, 497])
    parser.add_argument("--cutoffs", type=float, nargs="+", default=[0.7, 1.4])
    parser.add_argument(
        "--engines",
        choices=["numpy", "numba", "rust"],
        nargs="+",
        default=["numpy", "numba"],
    )
    parser.add_argument(
        "--models", choices=["GNM", "ANM"], nargs="+", default=["GNM", "ANM"]
    )
    parser.add_argument("--extension", type=Path)
    parser.add_argument(
        "--public-structure",
        type=Path,
        help="Measure public models on this molecular file; node counts come from its CA selection",
    )
    parser.add_argument(
        "--native-module", choices=["_rust", "_enm_prototype"], default="_rust"
    )
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--solve", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if min(args.sizes + [args.threads, args.trials, args.repeats]) < 1 or any(
        not math.isfinite(cutoff) or cutoff <= 0 for cutoff in args.cutoffs
    ):
        parser.error("sizes, counts, threads and cutoffs must be positive")
    if args.public_structure and args.extension:
        parser.error("public models load their bundled engine; do not pass --extension")
    if "rust" in args.engines and not args.extension and not args.public_structure:
        parser.error("--extension is required for Rust")
    if "rust" in args.engines and args.threads != 1:
        parser.error("the serial Rust constructor requires --threads 1")
    extension = args.extension.resolve(strict=True) if args.extension else None
    cases = []
    for n, cutoff, model, engine, trial in itertools.product(
        [None] if args.public_structure else args.sizes,
        args.cutoffs,
        args.models,
        args.engines,
        range(args.trials),
    ):
        case = dict(
            nodes=n,
            cutoff_nm=cutoff,
            model=model,
            engine=engine,
            trial=trial,
            seed=args.seed,
            threads=args.threads,
            repeats=args.repeats,
            solve=args.solve,
            native_module=args.native_module,
        )
        if args.public_structure:
            case.update(
                workload="public-model",
                structure=str(args.public_structure.resolve(strict=True)),
            )
        try:
            result = run_case(case, extension)
        except subprocess.CalledProcessError as exc:
            print(exc.stderr, file=sys.stderr)
            raise
        cases.append(result)
        print(
            f"{model} N={result['nodes']} cutoff={cutoff} {engine} trial={trial} complete",
            file=sys.stderr,
        )
    report = {
        "schema": "elastnetmt.enm_benchmark@1",
        "source_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
        ),
        "python": sys.version,
        "platform": platform.platform(),
        "extension_sha256": hashlib.sha256(extension.read_bytes()).hexdigest()
        if extension
        else None,
        "cases": cases,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    # Workers use the exact parent interpreter and write structured results to
    # a private file: provider stdout cannot corrupt the JSON protocol.
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        if json.loads(sys.argv[2]).get("workload") != "public-model":
            sys.path.insert(0, str(ROOT))
        Path(sys.argv[3]).write_text(
            json.dumps(worker(json.loads(sys.argv[2]), sys.argv[4]))
        )
    else:
        main()
