# Installed public ANM measurements, 2026-10-10

The integration at `03b81d056fff0e51850a0d2d2f57f9edee1b815a` is measured with
nine fresh processes: three trials each for NumPy (`vectorized`), Numba
(`parallel`) and Rust (`rust`). Each constructs an ANM from local TcTIM (1TCD),
497 alpha-carbon nodes, cutoff 1.2 nm, then calls public `get_modes()` once and
three more times. The exact installed wheel is used outside the checkout's
import path; workers do not inject source. Native digest:
`3f11d208cec8fd67f9826834f387547ed5e2ae519df16c83d01d4c3bacc451ad`.
Wheel digest: `589a1a9841f490cb4f976b146d006eb68a3912293bf5154615744fdcb0ac8824`.

Linux x86_64, Python 3.14.7, NumPy 2.4.6/MKL 2025.3. Registered BLAS/OpenMP
threads and Numba are limited to one; owned Rust construction is serial.
MolSysMT contact/preparation workers retain the public model defaults, and are
not claimed to be inspected by threadpoolctl. Initialization includes all model
preparation, conversion, selection, validation and contacts; its cost is not
attributed to one provider operation without a separate profile.

Median wall seconds (three independent processes per engine):

| Engine | Initialization | First `get_modes()` | NumPy eigh within query | Initialization + query |
| --- | ---: | ---: | ---: | ---: |
| NumPy | 4.898 | 0.757 | 0.694 | 5.655 |
| Numba | 4.844 | 2.397 | 0.706 | 7.241 |
| Rust | 4.867 | 0.704 | 0.689 | 5.571 |

Rust's first query is about 3.40× faster than Numba with JIT included, and
about 7% shorter than NumPy. Actual initialization-plus-query time is about
23% shorter than Numba and 1.5% shorter than NumPy. Imports take roughly
0.59–0.61 s additionally; process startup is excluded. These are observations
for this input/machine, not universal speed factors or confidence intervals.
NumPy eigh remains unchanged; its timing variation is not a Rust solver gain.
The roughly 4.9 s preparation dominates this particular first model use and
is a separate profiling target. These are first queries in new interpreters,
not cold OS disk/cache measurements.

All queries pass the model's physical spectrum validation and return finite
modes. Cached queries have median wall times about 2.2–2.6 microseconds and
do not diagonalize again. They are not repeated matrix constructions. No NumPy
parity allocation is inserted before the measured public query. Process-lifetime
peak RSS after the query is about 636 MiB for NumPy/Rust and 742 MiB for Numba;
it includes imports, preparation, output, eigensolver and compiler. This whole
model peak does not establish an isolated construction-memory saving over
NumPy. The earlier [construction samples](rust_enm_2026_10_10.md) remain separate.

All raw samples, threadpool identities, input checksum, clean orchestrator source
identity and installed native/wheel digests are in
[the JSON record](rust_public_anm_2026_10_10.json). Absolute paths are replaced
with installation/data labels; threadpool library filenames remain. The native
binary was built locally from source matching the committed crate/lock/build
contracts and separately passed all 189 installed tests with unchanged hashes.
Compatible primary Suite providers were used; this is not a fresh public
installation or completed hosted cross-platform admission.

Reproduce after installing the compatible runtime, using the interpreter that
resolves the intended installed wheel:

```bash
python devtools/enm_benchmark.py --public-structure /path/to/1tcd.pdb --models ANM --cutoffs 1.2 --engines numpy numba rust --threads 1 --trials 3 --repeats 3 --output .cache/rust-enm/public-model.json
```

Native CI/Conda delivery remain under #26/#18/#19 and MolSysSuite #113.
