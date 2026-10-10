# Performance and scalability

Size decisions need actual coordinates, contact density, available memory,
thread/backend configuration and the requested observable. No universal
workstation node ceiling is qualified. Use the
[reproducible benchmark](benchmarks/rust_enm_2026_10_10.md) and
[tool contracts](../devtools/rust_enm/README.md).

## Dense storage and solve cost

A float64 Kirchhoff matrix occupies `8 * N²` bytes. The ANM Hessian is
`3N × 3N`, so its output alone occupies `72 * N²` bytes. Contacts,
construction temporaries, eigenvectors, solver workspace and process imports
increase total memory. For example, a 5000-node ANM output alone is 1.8 GB
(decimal), which is not evidence that a full solve fits or completes.

The current NumPy Hessian allocates dense displacement/outer-product buffers
and off-diagonal blocks. Numba and the experimental Rust loop avoid those
intermediates, while still producing a dense output. A faster constructor
does not make the dense eigensolver sparse or change its cubic arithmetic cost.

## Reuse and resource policy

Model spectral queries reuse cached results. Contact rebuilding invalidates
spectra and fitted observables through the owned model reset operations.
Consumers should choose meaningful coarse-grained nodes and requested
observables before allocating large matrices. Native implementations must
honor explicit resource policy rather than consuming every core by default.

The current Rust prototype is serial and compared against one-thread Numba
and BLAS. The repeated-process study covers 64, 256 and 497 synthetic nodes
at two cutoffs. Those are measured workloads, not maximum supported sizes.
Its RSS measurements are process-lifetime high-water marks; do not label
their differences as exact kernel allocation or a leak diagnosis.

## Larger systems

Sparse/partial eigensolvers require a separate convergence and scientific
contract: truncated observables, null modes, mode ordering and degenerate
eigenspaces need appropriate guards. A Rust port alone does not qualify
large-system behavior. Installed native support and public delivery remain
tracked separately in #18/#19/#26.
