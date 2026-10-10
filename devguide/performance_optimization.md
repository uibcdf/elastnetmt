# Performance optimization

Use [the reproducible ENM construction study](benchmarks/rust_enm_2026_10_10.md)
and its raw samples before choosing a backend. Current public CPU routes are
NumPy and optional Numba; auto chooses Numba when discoverable. The Rust
construction crate is a development prototype tracked in #26.

## Measure operations separately

Separate process/scientific imports, molecular conversion and public MolSysMT
contacts, engine import, first/warm matrix construction, dense eigh and model
observables. The matrix operations belong to `_private/matrix_kernels.py`
and `_private/numba_kernels.py`; models consume those owned tools. Contacts
and interpolation remain provider operations.

Dense matrix construction/storage scale quadratically with node count; full
dense eigendecomposition has cubic arithmetic cost. Neither Numba nor Rust
changes those asymptotic limits. Cached model queries reuse eigenpairs rather
than rebuilding or solving. Cutoff/selection changes invalidate that cache.

## Measured Rust tradeoff

With 497 synthetic ANM nodes, one-thread MKL/Numba/Rust and three fresh-process
trials, median warmed Rust construction is 2.1–2.8 ms, compared with
59.7–69.0 ms for the existing NumPy operation and 1.9–2.2 ms for Numba.
First Rust construction is about 11–12 ms; first Numba construction including
JIT is about 1.9–2.0 s. These are kernel-boundary timings, not a full model
latency or a general machine-independent speedup. NumPy eigh remains about
0.73–0.80 s in those ANM samples and is the dominant repeated solve cost.

Rust snapshots/validates arrays before releasing the GIL and avoids NumPy's
dense construction intermediates. Its measured process construction RSS is
lower, but includes imports and compiler/backend overhead; it is not an
isolated allocation count. GNM NumPy is already competitive and outperforms
the prototype in several warmed construction cases.

The evidence supports targeted ANM construction and predictable first-use
latency. Preserve NumPy as a candidate, compare dense solvers separately and
qualify public model semantics/native installation before changing production
dispatch. A faer solver has not been benchmarked here.

## GPU and historical claims

The existing CuPy route offloads diagonalization while constructing matrices
on CPU. GPU throughput, transfer costs and usable node sizes depend on the
actual payload/device and need their own measurements. No generic GPU
multiplier or universal node threshold is established by this study.

This maintained guide replaces earlier unrecorded timing/multiplier and
exponential-scaling claims. The bundled 1TCD reference is Trypanosoma cruzi
triosephosphate isomerase (TcTIM); the former T4 lysozyme label was incorrect.
The linked current study uses synthetic networks and records that distinction.
