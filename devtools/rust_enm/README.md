# ENM construction prototype and measurements (#26)

This development crate implements serial Kirchhoff/Hessian construction through
PyO3 and rust-numpy. It is excluded from the ElastNetMT distribution and is not
a selectable public model engine. Root packaging/dependencies remain unchanged.
The Python models use the extracted operations in
`elastnetmt/_private/matrix_kernels.py`; contacts and interpolation remain with
their public MolSysMT/LinDelINT providers and diagonalization remains NumPy.

## Kernel contract

`build_kirchhoff(contacts)` accepts a bool NumPy array of shape `(N, N)`, symmetric
with a false diagonal, and returns a new float64 graph Laplacian.
`build_hessian(coords, contacts)` also accepts float64 `(N, 3)` finite positions
in numeric nanometers and returns a new `(3N, 3N)` Hessian in node-major XYZ order.
Contact distances squared must be finite and positive. C, Fortran and strided
arrays are supported. Wrong dtypes fail with TypeError; invalid shapes/contact
geometry fail with ValueError. Disconnected graphs and empty arrays are valid
matrix inputs; the public model owns minimum-node/nullspace/error policy.

Inputs are copied before detached computation; outputs own their storage. The
kernel runs at one thread, releases the GIL and does not create a pool. Boundary
validation and snapshots are included in measurements, alongside allocation
and arithmetic. NumPy/Numba matrix tools assume already validated inputs;
the comparison therefore includes the prototype's extra boundary checks.
No Rust eigensolver or public compatibility/admission claim is made.

## Build and installed-prototype gate

Use the suite Python 3.14 environment and a Rust toolchain. This crate pins
PyO3/rust-numpy 0.29.0, with a committed Cargo.lock, matching the inspected
sibling dependency generation. Build output and the Cargo cache are task-owned:

```bash
export CARGO_HOME="$PWD/.cache/rust-enm/cargo"
export CARGO_TARGET_DIR="$PWD/.cache/rust-enm/target"
export PYO3_PYTHON="$(command -v python)"
cargo build --locked --release --manifest-path devtools/rust_enm/Cargo.toml
cargo test --locked --manifest-path devtools/rust_enm/Cargo.toml --no-default-features
cargo fmt --manifest-path devtools/rust_enm/Cargo.toml --check
ELASTNETMT_RUST_PROTOTYPE="$CARGO_TARGET_DIR/release/lib_enm_prototype.so" python -m pytest --receptor=llm devtools/tests/test_rust_prototype.py
```

The displayed extension path is Linux; use the actual native library produced
on the platform under test. Loading uses that exact path. An explicit missing
or invalid native file fails; without the variable ordinary tooling checks skip
the development-only installed gate. A designated gate must set the path and
execute every native test without skips. ABI3 features follow the
[PyO3 build contract](https://pyo3.rs/v0.29.3/building-and-distribution); enabling
them is not evidence of installed-byte support on other Python/OS combinations.
No shared environment or sibling checkout is modified. Review and remove these
task-owned caches once native build/measurement work no longer needs them.

## Reproducible process measurements

`devtools/enm_benchmark.py` owns fresh-process orchestration. `load_prototype(path)`
loads an explicitly requested native file. `run_case(case, extension=None)`
executes one case with the parent's interpreter, explicit thread environment
and cleaned temporary worker resources; engine/validation failures propagate.

The CLI varies node count, cutoff, model and engine, with independent processes
for each trial. Seeded uniform 3D points have roughly constant number density
and explicit nanometer units. Public MolSysMT contacts use the requested thread
count; no private provider kernels are called. These synthetic networks expose
density/memory variation and are not protein throughput predictions.

```bash
python devtools/enm_benchmark.py --sizes 64 256 512 --cutoffs 0.7 1.4 --engines numpy numba rust --extension .cache/rust-enm/target/release/lib_enm_prototype.so --threads 1 --trials 3 --repeats 3 --solve --output .cache/rust-enm/comparison.json
```

NumPy, Numba, threadpoolctl and the compatible suite providers must be installed
in that interpreter. Normal NumPy/Numba runs need no Rust toolchain or extension.
The serial native comparison requires `--threads 1` for all engines. Report
fields separate scientific imports, contact preparation, selected-engine import,
first construction (including Numba JIT), repeated construction and NumPy eigh.
"First" is first kernel use in a new interpreter, not an OS cold disk/cache.

Memory is the process-lifetime RSS high-water mark on Linux/macOS, converted
to bytes (None on unsupported systems), not an isolated allocation counter.
Construction's RSS is captured **before** parity or solve and includes imports,
inputs, backend loading, JIT/temporaries and output; solve RSS is also affected
by the preceding NumPy parity reference. Repeated matrices are released before
the next allocation. No peak difference is claimed as kernel-only memory.
Raw samples, threadpool/backend identity, matrix bytes, source revision/dirty
status and native binary SHA256 are retained. Timing assertions are deliberately
absent from ordinary CI. Native properties and full model contracts qualify
correctness separately from the performance samples.

The prototype remains an evaluation under #26. Integration requires positive
evidence, compatible engine selection/thread/error policy, model-level science,
platform-native build/resources and installed gates coordinated with #18/#19.
The local diagnostic benchmark adds no scientific attribution integration;
Ackredit remains an application-owned optional boundary.
