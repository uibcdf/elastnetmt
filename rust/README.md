# Owned ENM matrix kernels

This crate builds private `elastnetmt._rust` through PyO3, rust-numpy and
setuptools-rust. Public GNM/ANM accept `engine="rust"`; `auto` selects the same
serial constructor with NumPy eigendecomposition. `vectorized`, `parallel` and
`gpu` retain their NumPy, Numba and CuPy meanings. The installed extension is
required and imported lazily on construction; missing/broken loads propagate
without substitution. Public MolSysMT owns contacts and LinDelINT interpolation.

## Kernel contract

`build_kirchhoff(contacts)` accepts bool `(N, N)` NumPy contacts, symmetric with
a false diagonal, and returns a new float64 graph Laplacian.
`build_hessian(coords, contacts)` additionally accepts finite float64 `(N, 3)`
positions in numeric nanometers and returns a new `(3N, 3N)` Hessian in node-major
XYZ order. Contact distances squared must be finite and positive. C/Fortran/
strided layouts are supported. Wrong dtypes raise TypeError; invalid shapes or
geometry raise ValueError. Boolean contacts use NumPy logical truth for any
nonzero storage byte, normalized through a uint8 view before constructing Rust
booleans; input bytes remain unchanged (see rust-numpy #509).
Disconnected/empty matrix inputs are valid; the model
owns minimum-node, nullspace and typed scientific error policy.

Inputs are snapshotted before detached computation and outputs own storage.
Rust releases the GIL, runs at one thread (`NUM_THREADS = 1`) and creates no
pool. Dense matrix memory is O(N²); NumPy eigh remains O(N³). The constructor
does not modify application thread environments or unit policy.

## Build and qualification

Source builds require Rust/Cargo. Build isolation supplies Python dependencies
from `pyproject.toml`. Cargo.lock pins PyO3/rust-numpy 0.29.0; `abi3-py311` and
setuptools' `py-limited-api = cp311` select the stable ABI floor. Compilation
alone does not qualify other platforms/interpreters. Source archives include
the Rust crate/lock and both Python distribution roots.

Use task-owned Cargo/output directories during development:

```bash
export CARGO_HOME="$PWD/.cache/rust-enm/cargo"
export CARGO_TARGET_DIR="$PWD/.cache/rust-enm/target"
export PYO3_PYTHON="$(command -v python)"
cargo fmt --manifest-path rust/Cargo.toml --check
cargo clippy --locked --manifest-path rust/Cargo.toml --no-default-features -- -D warnings
cargo test --locked --manifest-path rust/Cargo.toml --no-default-features
python -m build --sdist --outdir .cache/rust-enm/sdist
python -m pip wheel .cache/rust-enm/sdist/*.tar.gz --no-deps --wheel-dir .cache/rust-enm/wheels
```

Provision a compatible complete suite environment before installing the wheel.
The required scientific selector is `tests/physical/test_native_matrix_kernels.py`
(no optional skips). Existing model physics/calibration/unit/error/state and
trajectory guards execute through NumPy and Rust. CI builds one wheel per
Linux/macOS arm64 platform and installs those same bytes on Python 3.11–3.14.
The complete suite runs in a temporary directory with tests/governance inputs
and neither Python package source root. `devtools/native_wheel.py` verifies
all declared runtime/native hashes before/after science, version and import
origin. Hosted qualification/public admission remain #19; native Conda delivery
remains #18 and [MolSysSuite #113](https://github.com/uibcdf/molsyssuite/issues/113).
No public release is selected; historical noarch callers are suspended.

## Reproducible construction measurements

`devtools/enm_benchmark.py` owns fresh-process orchestration with explicit
MKL/OMP/OpenBLAS/Numba limits. `load_native(path, module_name="_rust")` loads
exact bytes. `load_prototype(path)` retains the old init name for historical
samples; the development crate has been retired. `run_case(case, extension=None)`
uses the same interpreter and managed worker files/caches. Failures propagate.

```bash
python devtools/enm_benchmark.py --sizes 64 256 497 --cutoffs 0.7 1.4 --engines numpy numba rust --extension .cache/rust-enm/target/release/lib_rust.so --threads 1 --trials 3 --repeats 3 --solve --output .cache/rust-enm/comparison.json
```

The displayed library path is Linux; use the actual built file on the tested
platform. NumPy/Numba/threadpoolctl and compatible suite providers must be
installed. Comparison requires one thread for all engines. Synthetic uniform
3D points have fixed density and explicit nm units; public MolSysMT computes
contacts. Rust validates/snapshots inputs; NumPy/Numba assume validated buffers.

Fields separate imports, contacts, backend loading, first construction (Numba
JIT included), warmed construction and optional NumPy eigh after parity. RSS is
the process-lifetime high-water mark before parity/solve, including imports,
inputs/output, backend loading and temporaries; it is not kernel-only memory.
First use means a new interpreter, not an OS cold disk. Raw samples, threadpool
identity, source revision and binary hashes are retained. Historical measurements
are in `devguide/benchmarks/rust_enm_2026_10_10.md`; original byte/source identities
are unchanged. Matrix speedups do not establish equal whole-model speedups.
Ordinary CI has no timing threshold. Ackredit remains an optional application
attribution boundary; this backend adds no eager provider registration.

Explicit Numba remains during installed qualification under #26; maintainers
review coexistence by 2026-11-10. Remove task-owned caches/build resources when
qualification and measurements no longer need them.

The same tool can time initialization and the first/cached `get_modes()` queries
on a real molecular file through the installed public models:

```bash
python devtools/enm_benchmark.py --public-structure /path/to/1tcd.pdb --cutoffs 1.2 --engines numpy numba rust --threads 1 --trials 3 --repeats 3 --output .cache/rust-enm/public-model.json
```

Provision/install the runtime being compared before invoking this mode; workers
do not inject the checkout into the import path. The output records the actual
runtime file and native digest. NumPy eigh is timed transparently, and repeated
cached queries must not diagonalize again. Initialization includes the public
MolSysMT contact defaults (these provider workers are not a threadpoolctl claim).
Registered BLAS/OpenMP and owned Rust/Numba threads are bounded as above. These
measurements perform no matrix parity allocation before the solve and report
actual initialization-plus-first-query time separately from imports/process
startup. Each fresh process represents a first query, not a cold OS disk cache.
