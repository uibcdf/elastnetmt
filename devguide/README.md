# ElastNetMT Developer Guide

Welcome to the **ElastNetMT** developer guide. This document serves as the entry point for understanding the technical philosophy, architecture, and standards of the library within the **MolSysSuite** ecosystem.

## Vision

ElastNetMT is the dynamic engine of the MolSysSuite. While **MolSysMT** provides the structural foundation, ElastNetMT breathes life into those structures by studying their intrinsic dynamics through Elastic Network Models (ENM). Our goal is to provide a physically rigorous yet computationally efficient framework to explore protein flexibility, vibrational modes, and conformational changes.

## Guiding Principles

- **Physical Rigor:** Every algorithm must be grounded in established ENM theory (Gaussian and Anisotropic models).
- **Interoperability:** Seamlessly consume objects from `molsysmt` and produce visual states for `molsysviewer`.
- **Dimensional Consistency:** All physical quantities must be handled via `pyunitwizard`.
- **Structured Diagnostics:** All warnings and errors must follow the `smonitor` standard.

## Installation for Development

To install ElastNetMT for development, it is recommended to use the following command to avoid dependency conflicts:

```bash
pip install --no-deps --editable .
```

- [Architecture](architecture.md): Class hierarchy and data flow.
- [Roadmap](roadmap.md): Technical milestones toward version 1.0.0.
- [ElastNetMT Add-on Plan](elastnetmt_addon_plan.md): Development plan for the MolSysViewer add-on implemented from this repository.
- [ElastNetMT Add-on Demo](elastnetmt_addon_demo.md): Minimal reproducible flow for exercising the in-tree MolSysViewer add-on.
- [ElastNetMT Add-on Follow-up](elastnetmt_addon_follow_up.md): Short follow-up note after delivering the initial add-on MVP and host integration.
- [Mathematical Foundations](mathematical_foundations.md): Kirchhoff and Hessian matrices, spectral analysis.
- [SMonitor Integration](smonitor_integration.md): Diagnostic codes and signals.
- [Units and Conventions](units_and_conventions.md): Physical quantities and force constants.
- [Visualization Protocols](visualization_protocols.md): Rendering springs and normal modes.
- [Testing Strategy](testing_strategy.md): Tiers of verification (Smoke, Physical, Regression).
- [Pending proposals](pending_proposals/README.md): Open issue-backed proposals.
