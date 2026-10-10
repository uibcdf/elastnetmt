# Public ANM preparation profile, 2026-10-10

The measured wheel remains the native integration qualified under #26. The
clean measurement tool is `de4cc1e86b630793f5c83f0d72dfecef0060b01e`.
Three fresh workers each construct an ANM from the original local 1TCD PDB
(497 CA nodes, 1.2 nm cutoff), then construct three independent models from
the file and three from the first model's public `molecular_system`. They
retain public conversion, argument digestion, selection and coordinate
validation. No spectral query runs in this preparation-only workload.

Median wall seconds (median of three process medians for repeated cases):

| Input / process state | Initialization |
| --- | ---: |
| PDB, first model in a fresh worker | 5.358 |
| Same PDB, repeated models in that worker | 0.764 |
| Already converted MolSys, repeated models in that worker | 0.089 |

The prepared-input path takes about 8.6 times less initialization time than
repeated PDB parsing in these samples. It presupposes an existing converted
system and warmed provider modules. It does not make a fresh PDB workflow
start in 0.089 s, accelerate diagonalization or measure an isolated Rust kernel.
Model creation still allocates/converts its state and validates inputs. Exact
node order and every contact agree across inputs; the prepared system's
coordinates and the first model's contact map remain unchanged.

Linux x86_64/Python 3.14.7, NumPy 2.4.6/MKL 2025.3. Registered BLAS/OpenMP
workers are limited to one. MolSysMT retains its public contact configuration;
threadpoolctl does not establish all provider worker counts. Machine load
varies: these first-use times must not be treated as a regression or improvement
against the earlier 4.9 s samples from another measurement session. Process
startup and imports are excluded; imports are recorded separately.

A separate fresh worker profiles only first initialization. Its 8.674 s wall
time includes cProfile overhead and is excluded from the table. The dominant
causal path is:

1. `digest_to_form` requests MolSysMT's lowercase form dictionary.
2. That dictionary enumerates `LazyRegistry.keys()`.
3. DepDigest scans/imports all eligible form adapters, registering their
   argument-digestion wrappers (5.271 s cumulative in this profiled worker).
4. The actual PDB-to-MolSys conversion then prepares topology and coordinates
   (2.388 s cumulative).

These nested cumulative rows overlap and must not be summed. cProfile covers
the calling thread, not native worker internals. The registry behavior follows
its existing whole-registry lazy contract; this is a provider-owned improvement,
not evidence of a broken DepDigest API. MolSysMT owns its form-validation route:
[molsysmt#382](https://github.com/uibcdf/molsysmt/issues/382) retains the proposal.
Its existing PDB/bond-policy work under #304 is separate. No private provider
registry, skipped validation or custom PDB parser is added to ElastNetMT.

The [JSON record](public_preparation_2026_10_10.json) retains all unprofiled
samples, a separately labelled bounded profile, source/provider identities,
input checksum, installed distribution versions and wheel/file digests.
Distribution version metadata and actual editable provider commits are recorded
separately. The wheel is normally installed outside the checkout; all 43 owned
Python/native files match before and after measurement. Its SHA256 is
`589a1a9841f490cb4f976b146d006eb68a3912293bf5154615744fdcb0ac8824`.
Compatible primary Suite providers are used; this is local evidence, not public
delivery or qualification of newer provider commits.

Reproduce with the intended installed runtime on the worker's import path:

```bash
python devtools/enm_benchmark.py --public-structure /path/to/1tcd.pdb --preparation-only --models ANM --engines rust --cutoffs 1.2 --trials 3 --repeats 3 --output preparation.json
python devtools/enm_benchmark.py --public-structure /path/to/1tcd.pdb --preparation-only --profile-preparation --models ANM --engines rust --cutoffs 1.2 --trials 1 --repeats 3 --output preparation-profile.json
```

For repeated independent models, convert the file once with public MolSysMT
and pass the resulting MolSys. For one model with successive cutoffs, the
existing `calculate_contacts(cutoff=...)` reuses its converted system and
invalidates dependent spectra/calibration. Each new graph must still meet its
model's physical conditions when solved.
