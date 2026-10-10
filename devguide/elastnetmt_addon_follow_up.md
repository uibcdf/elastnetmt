# ElastNetMT Add-on Follow-up Note

This note records the state of the MolSysViewer add-on work after the initial MVP was implemented and pushed.

## Delivered

The following pieces are already delivered from the **ElastNetMT** repository:

- the in-tree package `molsysviewer_elastnetmt`,
- add-on lifecycle, runtime cache, demo helpers, workbench helpers, and export helpers,
- real rendering of:
  - contact links,
  - ANM mode vectors,
  - anisotropy ellipsoids,
- integration tests for the add-on MVP against `pdb_id:1tcd`,
- developer documentation for plan, demo, and roadmap state.

## Host Dependency Already Landed

The minimum corresponding host work has also been integrated in **MolSysViewer**:

- `entry` for add-on workbench sections and export helpers is now resolved to Python callables when available,
- runtime summaries are refreshed after add-on context actions,
- export messages include the materialized add-on runtime summary.

This means the add-on is no longer only declarative. The host already consumes the Python-side helper layer.

## Molecular input and model cache, 2026-10-10

The default molecular input for contact, ANM and anisotropy adapters and the
model panel is public `view.molsys`. MolSysViewer exposes its normalized
`molsysmt.MolSys` through this property, independently of the original input
form. Explicit `molecular_system=` inputs remain supported through MolSysMT.

`runtime.get_or_build_model` owns cache reuse for both model builders. Source
replacement clears all cached models. Before reuse, it re-evaluates the node
selection, extracts the requested frame through MolSysMT, compares coordinates,
periodic box and experimental B factors exactly in common units, and delegates
topology comparison to `msm.compare`. This protects motions across a contact
threshold even when approximate coordinate comparison would report equality.
An invalid or unloaded input raises instead of returning an old model.
Invalidation occurs on the next model request; this does not implement an
automatic scene-change callback or frontend redraw.

Runtime summaries contain UI state and cache keys, excluding molecular objects
and dense matrices. Reusing unchanged inputs retains the existing model and
its spectra. Molecular conversion, selection, extraction and comparison remain
MolSysMT operations; ElastNetMT owns this ENM-specific reuse decision.

Actual-provider regression cases are maintained in
`tests/integration/test_addon_model_cache.py`, covering both builders, explicit
PDB inputs, scene replacement/addition, mutable coordinates/topology/B factors,
periodic boxes, multiple frames and the model panel's public input boundary.
Provider findings from this review are tracked in
[MolSysMT #383](https://github.com/uibcdf/molsysmt/issues/383) (scalar atom IDs)
and [#384](https://github.com/uibcdf/molsysmt/issues/384) (B-factor frame access).

A bounded warm Linux/Python 3.14 installed-wheel probe on the bundled 497-node
1TCD ANM measured a median 0.312 s for validated cached requests with existing
modes (five calls), versus 0.822 s for fresh models with modes (three builds).
The comparison includes cache-input validation and excludes cold preparation
and rendering; it is not a cross-platform performance claim. Raw timings are
in `devguide/benchmarks/addon_cache_2026_10_10.json`.

## What Remains Open

The most relevant open items are:

1. Improve the MolSysViewer workbench UI so enriched `runtime_payload` data is shown more explicitly.
2. Add broader end-to-end export and replay checks across both repositories.
3. Decide whether `molsysviewer_elastnetmt` remains in-tree or becomes a separate distribution.
4. Design a richer parameter-editing surface once the current Python-driven flow is considered stable.

## Current Recommendation

Do not widen scope yet. The correct next step is to polish host presentation and replay reliability before attempting a richer frontend or extraction into a separate package.
