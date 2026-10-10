---
summary: Evaluate Rust for owned ENM kernels with measured workload and delivery contracts.
issue: uibcdf/elastnetmt#26
status: active
opened: 2026-10-10
closed:
verification: measured
area: [performance, distribution]
guard: devtools/tests/test_rust_prototype.py
normative: devtools/rust_enm/README.md
blocked_by: []
supersedes: []
---

# Rust study for ElastNetMT

The initial assessment below is retained as historical evidence. Current
implementation and measurement state appears in the dated checkpoints.

## What

The maintainer requested review of the sibling Rust migration. The inspected
MolSysMT checkout is clean at 8ae160fc93ed5bc815bcc24b37c2875ba735623d and
behind its remote by 39 commits; it is preserved without checkout/update.
Its rust/ crate is integrated through setuptools-rust and PyO3 into
molsysmt._rust, with NumPy buffers, Rayon and faer. The old Numba runtime was
retired. The editable version string is stale and is not source identity.

ElastNetMT's owned kernels construct Kirchhoff/Hessian matrices through
NumPy/Numba. Contacts remain a public MolSysMT operation; its inspected CPU
path uses native Rust neighbors or distances. Dense spectral queries already
call compiled NumPy eigh. Production native packaging would supersede the
current pure-Python noarch candidate classification.

## How: bounded local measurement

Initial exploration: Python 3.14.7, NumPy 2.4.6,
OPENBLAS_NUM_THREADS=1, NUMBA_NUM_THREADS=2. This did not limit the actual
MKL backend; those first samples are exploratory, not a one-BLAS-thread result.
One process loads MolSysMT's installed data/pdb/1tcd.pdb, then builds each
GNM/ANM with vectorized and parallel engines. It uses 497 alpha-carbon nodes.
For each route: time initialization, then reset spectral state before one
first and three repeated solves. Temporarily wrap numpy.linalg.eigh to time
the native spectral call. Each solve checks finite eigenvalues and the model's
existing spectrum guard remains active.

| Route | First solve (s) | Repeated solve samples (s) | Repeated eigh samples (s) |
| --- | --- | --- | --- |
| GNM NumPy | 0.036405 | 0.023010, 0.020250, 0.020191 | 0.021026, 0.019132, 0.019131 |
| GNM Numba | 1.407824 | 0.019614, 0.019104, 0.018637 | 0.018451, 0.017822, 0.017457 |
| ANM NumPy | 0.310480 | 0.295682, 0.298002, 0.298038 | 0.229230, 0.230379, 0.230561 |
| ANM Numba | 1.474695 | 0.241566, 0.246463, 0.243345 | 0.235837, 0.240323, 0.236926 |

Initialization times were 5.184716/0.797173/1.151039/0.831090 s respectively.
They combine import/data conversion, selection, coordinate validation and
contacts; they are order-dependent and are not isolated contact benchmarks.
The non-eigh difference includes matrix construction, provider coordinate
retrieval, validation and telemetry; it is not pure kernel timing.

## Why and interpretation

Numba's first solve has about 1.2–1.4 s of non-eigh latency. This is consistent
with first-use JIT cost and motivates an ahead-of-time prototype. Repeated ANM
Numba solves spend about 98% in eigh. Replacing a construction kernel alone
therefore has limited steady-state leverage for this one payload, while Rust
may improve cold start and avoid NumPy Hessian temporaries. No Rust ENM code
was executed; no Rust speedup is established. Memory was not measured.

The MolSysMT archived linear-algebra decision also records solver tradeoffs:
faer is not automatically faster than every BLAS/LAPACK build. Its timings
belong to those recorded machines and cannot be copied as ElastNetMT results.

## Proposed staged implementation

1. Retain an independently reproducible baseline with fresh-process cold
   latency, warmed samples, peak memory, several node counts, contact densities
   and controlled thread counts. Inspect the actual BLAS and native binary.
2. Prototype private owned Rust Kirchhoff/Hessian operations, with float64
   arrays, explicit numeric length conversion and a bounded threading contract.
   Keep unit/argument/error/state policy at the Python boundary. Reuse public
   MolSysMT contacts and provider interpolation; do not call their private Rust
   adapters or duplicate their algorithms.
3. Qualify symmetry, row-sum/rigid-nullspace, translation/rotation covariance,
   finite results, disconnected/underconstrained cases and calibration.
   Compare eigenvalues at tolerance and eigenspaces/residuals, allowing signs
   and rotations within degenerate eigenspaces.
4. Benchmark faer separately against the real NumPy backend before changing
   diagonalization. Sparse/partial solvers are a separate algorithmic decision
   requiring convergence and truncated-observable tests.
5. Classify native artifacts under the existing suite release controls.
   Prepare platform-specific wheel/Conda build, source archive/toolchain,
   Python 3.11–3.14 Linux/macOS arm64 installed-byte tests and public admission
   before claiming a delivered Rust route. Coordinate #18/#19; the current
   noarch plan does not qualify an embedded native extension.
6. Choose the production cut after measured benefit and complete science,
   consumer and installed gates. Track temporary coexistence and preserve
   accepted engine/API semantics; retire Numba only at the qualified cut.

## Scope and exclusions

This is a measured product proposal, not a new mandatory suite-wide Rust rule.
No sibling checkout/environment, native binary, public dependency pin,
distribution artifact or runtime engine is changed. Documentation remains
#8/#13/#25. Future portable/shared-tool gaps belong to their providers.

## Acceptance criteria

A reproducible workload baseline, a bounded prototype and justified backend
decision, independent scientific properties, threading/memory evidence and
a compatible installed-native delivery plan. This issue remains active until
those implementation/qualification decisions and gates are completed.

## Corrected bounded-thread measurement, 2026-10-10

Runtime inspection found MKL 2025.3 (Intel threading). Repeating the same
protocol with MKL_NUM_THREADS=1, OMP_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1
and NUMBA_NUM_THREADS=2 confirms MKL and OpenMP each report one thread through
threadpoolctl. This is Linux x86_64; the inspected MolSysMT native binary
SHA256 is c535c7d2f0e2a92b6ebf8298a60b19e4b5555467b4aa087e9563c6760619827e.
The binary digest identifies the local bytes, not a verified source-to-build link.

| Route | First solve (s) | Repeated solve samples (s) | Repeated eigh samples (s) |
| --- | --- | --- | --- |
| GNM NumPy | 0.043328 | 0.043468, 0.038173, 0.038231 | 0.041570, 0.037327, 0.037351 |
| GNM Numba | 1.368791 | 0.040455, 0.040404, 0.043422 | 0.037953, 0.037699, 0.040468 |
| ANM NumPy | 0.707655 | 0.702588, 0.700395, 0.695468 | 0.646802, 0.644798, 0.638990 |
| ANM Numba | 1.720635 | 0.650240, 0.648456, 0.645680 | 0.644191, 0.642724, 0.639899 |

Initialization samples: 5.034713, 0.707159, 1.044289, 0.730607 s in table order.
The bounded run preserves the conclusion: warm ANM Numba spends about 99%
in dense eigh; first-use non-eigh latency is about 1.1–1.3 s. These are
one-process samples, not independent-process confidence intervals.
Thread configuration changes materially affect solve time and must be recorded.
The staged baseline still needs peak memory, multiple sizes and fresh processes.

## Prototype implementation checkpoint, 2026-10-10

The owned NumPy matrix operations were extracted into
`elastnetmt/_private/matrix_kernels.py`; GNM and ANM call those reusable tools.
Their numerical formulas and public backend selection remain unchanged.
`devtools/rust_enm` is a separate serial PyO3/rust-numpy crate, not wired into
root packaging or public engine dispatch. Native matrix inputs are snapshotted
before releasing the GIL, layouts are supported explicitly and outputs own
their storage. NumPy eigh and public provider contacts/interpolation remain
unchanged. No shared environment or sibling repository is written.

`devtools/enm_benchmark.py` independently orchestrates fresh interpreters, public
MolSysMT synthetic contacts, explicit thread settings, first/warmed construction,
optional eigendecomposition and process RSS high-water marks before parity.
Its contract and executable commands are maintained in the crate README.
The Rust boundary validates and snapshots inputs while existing NumPy/Numba
operations assume already validated buffers; measured native overhead includes
that work. A requested missing native file or failed kernel is not replaced.

Local Rust unit tests pass 3/3. The installed Python prototype gate passes
13/13 on Linux/Python 3.14 (zero skips), alongside four independent NumPy matrix
properties. Guards cover spring energy, rigid motions, covariance, storage
layouts, disconnected/empty inputs and malformed buffers. Installed support
on other interpreters/platforms and public-model Rust execution remain open.
Full-process repeated measurements are recorded separately after execution;
one-case initial timings are not a final performance decision.

Temporary parallel implementations are an owner-local evaluation under #26,
responsibility: ElastNetMT maintainers. Review by 2026-11-10; remove the
development-only duplicate when the production engine/packaging decision is
qualified or the prototype is rejected. A production migration must replace
this exception with the accepted owned runtime and its installed gates.

## Repeated measured decision, 2026-10-10

All 108 fresh-process samples complete for GNM/ANM, 64/256/497 nodes,
0.7/1.4 nm cutoffs, NumPy/Numba/Rust, three process trials and three warmed
constructions per trial. Raw samples and aggregation are retained in
[the measured record](../benchmarks/rust_enm_2026_10_10.md). Thread inspection
confirms one thread for the compared native/JIT/BLAS routes.

At 497 ANM nodes, Rust warm construction is 2.073/2.799 ms versus NumPy
59.746/68.969 ms and Numba 1.876/2.227 ms (cutoffs 0.7/1.4 nm). First Rust
construction is 11.266/11.862 ms versus Numba 1970.521/1940.875 ms including
JIT. Rust wins cold and versus the allocating NumPy Hessian; it does not beat
warmed Numba here. GNM NumPy already performs well and must remain a candidate.
Construction phase process peak RSS is roughly 517–519 MiB with Rust,
564–566 MiB with NumPy and 638–639 MiB with Numba. These are whole-process
high-water marks including backend loading, not isolated kernel allocation.

Unchanged NumPy eigh takes roughly 0.73–0.80 s in these 497-node ANM samples.
No public-model end-to-end Rust speedup is established: the development tool
executes a parity reference before eigh, and public models still select the
existing engines. Dense NumPy intermediates and first-use JIT are justified
targets; moving diagonalization blindly is not. The late exact-file loader
hardening rejects Python substitutes and does not change native kernel bytes.

Maintained performance guidance now uses analytical memory/complexity and
linked reproducible samples, removing unverified GPU multipliers, exponential
scaling and workstation node ceilings. The reference protein is TcTIM (1TCD),
not the historical T4 lysozyme label. These new samples use synthetic geometry.

Next qualification: an owner-local production adapter/backend decision, full
model scientific/error/unit/state/trajectory tests, bounded parallelism if
needed, and native platform/install gates coordinated with #18/#19. Public
engine/API and installed-native admission remain open; retain this issue.

Final local validation: 138 tests pass for `tests` plus the four benchmark
contract guards. The final native-file loader passes all 13 installed-prototype
tests without skips. Rust unit tests (3), Clippy with denied warnings, formatting
and Ruff pass. Reporting indexes/protocol and the 17 actual immutable-SDK
distribution/source/CI-route assertions pass. The latter include corrected docs
workflow classification and the new pure-Python matrix resource.
