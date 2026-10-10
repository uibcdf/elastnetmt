---
summary: Add-on adapters reuse cached ENM models after replacing the molecular input.
issue: uibcdf/elastnetmt#27
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: high
verification: measured
area: [integration]
guard: tests/integration/test_addon_model_cache.py
normative:
blocked_by: []
supersedes: []
---

# Bind add-on models to the actual molecular input

## What

The contact and ANM adapters key `runtime.cached_models` by selection, cutoff,
structure index and syntax. They do not include or validate the molecular
source. MolSysViewer scene replacement preserves these cached consumer models.
An unchanged parameter set can therefore return an old graph/spectrum for a
new molecular system.

## How

Reproduced on Linux/Python 3.14.7 at ElastNetMT `c623fed`, MolSysMT
`8ae160fc93ed5bc815bcc24b37c2875ba735623d` and MolSysViewer
`c046fca173f501c6e259761ef8f3d6b1825f17e8`, using their actual public APIs:

1. Convert a four-CA tetrahedron PDB, with positions in angstroms
   `(0,0,0), (3,0,0), (0,4,0), (0,0,5)`, through `msm.convert`.
2. Copy through `msm.copy`, then move the fourth atom 2 nm along x using
   public `msm.get`/`msm.set`.
3. Load the first system in `MolSysView(debug_js=True)` and obtain cached
   contact/ANM models at the default 1.2 nm cutoff.
4. Replace it through `view.load(second, mode='replace')` and ask both adapters
   for models with the same parameters.

Both adapters return the exact previous model object. The cached contact
network has six undirected edges; a fresh `ElasticNetworkModel` built from
the current public `view.molecular_system` has three. The isolated-node
diagnostic is expected for the second network. No spectrum was requested for
that disconnected network; this does not claim successful ANM modes there.

## Why

Contact links and modes can describe an earlier structure while being displayed
on the current one. MolSysMT conversion/contacts are working in this case; the
defect belongs to ElastNetMT cache orchestration. Python-side reproduction does
not establish graphical frontend or cross-platform qualification.

## Ownership and acceptance

Keep molecular conversion, selection, coordinate/topology changes and frame
assembly in supported public MolSysMT operations. Keep ENM cache orchestration
in this consumer. Use supported input/viewer identity or change contracts;
request missing reusable provider capabilities with linked evidence rather
than accessing private provider structures or implementing a molecular
revision subsystem locally.

Preserve reuse for a genuinely unchanged source. Protect both adapters against
replacement and explicit alternate inputs with actual provider regression cases.
Review in-place coordinate/topology edits and scene additions; these additional
cases remain unexecuted. Preserve input state and existing spectrum/error
contracts. Resolve this report only with an executed mechanism guard.


## Resolution and public-input correction — 2026-10-10

The correct normalized public viewer boundary is `view.molsys`, confirmed in
MolSysViewer `c046fca173f501c6e259761ef8f3d6b1825f17e8`. The historical reproduction
above used `view.molecular_system`; that attribute need not have the MolSys form.
Both adapters and the model panel now consume public `view.molsys`, with explicit
alternate forms normalized by public MolSysMT conversion.

The shared `runtime.get_or_build_model` binds the cache to the source object and
validates cached ENM inputs through public MolSysMT selection, frame extraction,
attribute access and topology comparison. Coordinates, periodic boxes and
experimental B factors are compared exactly in common units. Replacements and
edited cached inputs clear the model cache. Unloaded or invalid inputs raise.
Runtime summaries exclude molecular systems and dense model objects.

The guard has 29 actual-provider regression cases. Both model builders preserve
unchanged reuse, reject stale models after real viewer replacement/addition and
explicit alternate inputs, and detect coordinate/topology/B-factor/box changes.
A tiny displacement across an actual contact threshold changes the graph even
though NumPy allclose considers the coordinates equal. Tests also cover chosen
frames/structure append, PDB inputs, edited cached cutoffs and the public panel
boundary. Invalidation is checked on the next adapter request; no automatic
frontend redraw or scene-change event contract is claimed.

A normal ABI3 wheel was built from the new source archive and installed outside
the checkout on Linux/Python 3.14.7. All 218 scientific, integration and reporting
tests passed without skips. All 42 owned Python/native file hashes matched the
wheel before and after tests and the cache timing probe. Python source bytes in
the wheel match the working implementation and compile successfully. The retired
Python 2 module and its repository archive text are absent from both artifacts.
This is local installed evidence, not a completed hosted platform matrix or
public support admission.

Provider observations are separately owned by MolSysMT #383 (scalar atom IDs)
and #384 (B-factor frame selection). This fix uses provider frame extraction
instead of copying or privately slicing molecular storage.
