# ElastNetMT Roadmap

This roadmap outlines the evolution of **ElastNetMT** from its current state to a high-performance, AI-ready dynamics engine for the **MolSysSuite**.

## Modernization priority, reviewed 2026-10-08

Complete the following maintenance sequence before the exploratory features
below. Source implementation, hosted qualification and public delivery are
separate milestones.

1. **Establish a measured baseline.** Inspect current suite policy, exact CI
   jobs and scientific assertions. The baseline is structurally conformant,
   but four Python 3.11/3.12 cells fail in LinDelINT's automatic fallback.
   TcTIM reference inputs must come from installed local data in tests.
2. **Repair core numerical and value contracts.** Stabilize GNM calibration,
   plot and cutoff state (#21); preserve application unit policy; activate
   ArgDigest value contracts and lazy DepDigest engine boundaries (#14).
   Protect symmetry, zero modes, rotation/translation invariance and physical
   trajectory amplitude. PR #22 at 6a3598a passed the eight-cell source matrix,
   viewer contract, suite policy and distribution governance on 2026-10-09.
3. **Qualify the consuming routes.** Use one published Pytest Receptor pin in
   full scientific CI and independent governance, exercise Numba parity with
   Numba installed, and inspect all eight source cells plus viewer contract.
   Track the vectorized interpolation default as a consumer workaround for
   lindelint#8, rather than claiming the provider automatic route is repaired.
4. **Complete scientific edge-case contracts.** Specify disconnected or
   underconstrained networks, duplicate/empty selections, absent or constant
   experimental B factors, and unavailable physical stiffness. Add mechanism
   tests and convergence/performance measurements before expanding solvers.
   The correction for #23 implements node/spectrum/profile contracts, explicit
   failures, candidate filtering and state preservation. Its complete hosted
   qualification is recorded in PR #22 after execution. Performance and larger
   solver work remain separate follow-up work.
5. **Refresh the complete documentation and add-on review.** The core GNM/ANM
   examples and units are updated in the first implementation. Remaining work
   includes obsolete notebooks/imports, copied API pages, complete public
   docstrings (#8), published documentation (#13), and viewer/export contracts.
6. **Qualify installed delivery.** Resolve compatible public sibling routes,
   commit a real release plan, qualify the exact candidate bytes outside the
   checkout across Python 3.11–3.14 on Linux/macOS arm64, and verify public
   installation before advertising support (#18/#19). Source CI alone does
   not complete this milestone.

## Phase 1: Structural Foundations & Suite Alignment
*Status: IMPLEMENTED IN PART; qualification and contract review remain open.*

- [x] **Inheritance Refactoring:** `ElasticNetworkModel` base class unifies `GNM` and `ANM`.
- [x] **Contact Map Centralization:** Moved to `_private/contacts.py` with unit-aware normalization.
- [x] **Suite Integration:** 
    - ArgDigest value registry and optional-engine DepDigest boundaries.
    - Integrated `lindelint` for full-atom trajectory generation.
- [x] **SMonitor Diagnostics:** Deep instrumentation for network integrity and spectral health.
- [x] **Tiered Testing:** Basic `smoke`, `physical` and `integration` tests implemented.
- [ ] **Complete Qualification:** All required source and installed routes reviewed.

## Phase 2: Performance & Physics Refinement
*Status: IN PROGRESS*

- [x] **Hessian Vectorization:** Implemented Level 1 (NumPy) and Level 2 (Numba).
- [x] **GPU Acceleration:** Level 3 (CuPy) implemented for spectral decomposition.
- [ ] **Lazy Evaluation Engine:** Refine dormant state triggers (Mostly done in Phase 1).
- [x] **B-Factor Engine:** Separate raw predictions and fitted scale; protect repeated fitting and final cutoff state (#21).

## Phase 3: Drug Discovery & Pocket Dynamics
*Focus: Integration with TopoMT and PharmacophoreMT.*

- [ ] **Ligand Perturbation:** Implement `model.add_ligand()` to add non-protein nodes to the Hessian matrix.
- [ ] **Pocket Breathing:** Develop tools to track pocket volume (TopoMT) along mode trajectories.
- [ ] **Dynamic Pharmacophores:** Define tolerance ellipsoids for pharmacophoric points based on local flexibility.
- [ ] **AI-Binder Ensembles:** Create standard exporters for conformational ensembles compatible with BindCraft and RFdiffusion.

## Phase 4: Scaling & Advanced Biology
*Focus: Supramolecular Scale and AI-Readiness.*

- [ ] **Large-Scale Solvers:** Implement iterative solvers for systems with >10k nodes (Ribosomes, Capsids).
- [ ] **Conformational Morphing:** Implement transition path prediction between Apo and Holo states.
- [ ] **Elastic Descriptors:** Build the featurization engine to extract "mechanical fingerprints" for ML models.
- [ ] **Quaternary Assembly:** Develop mechanical complementarity metrics for predicting protein-protein association.

## Cross-Cutting Track: MolSysViewer Add-on
*Status: IN PROGRESS*

- [x] **Add-on Skeleton:** `molsysviewer_elastnetmt` exists in-tree and is discoverable by MolSysViewer.
- [x] **Viewer Runtime:** Cached runtime for ENM state, overlays, and parameters is implemented.
- [x] **Overlay Adapters:** Contact links, normal mode vectors, and anisotropy ellipsoids are rendered through MolSysViewer shape primitives.
- [x] **Reproducible Controls:** Actions, workbench helpers, runtime snapshots, and export helpers capture explicit ENM parameters.
- [ ] **Extraction Readiness:** Keep the package layout compatible with a future split into `molsysviewer-elastnetmt`.
- [ ] **Host Presentation:** Improve MolSysViewer UI presentation of enriched add-on workbench and export payloads.

See [ElastNetMT Add-on Plan](elastnetmt_addon_plan.md) for the execution order and scope boundaries.

## Future Horizons
- **Mechanopharmacology:** Force-responsive drug design.
- **Environment-Aware ENM:** Temperature and pH-dependent elasticity.
- **QM/ENM Hybrids:** Quantum-level precision for ligand pockets.
- **Haptic Dynamics:** Real-time interactive manipulation in MolSysViewer.
