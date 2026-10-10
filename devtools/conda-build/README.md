# Native distribution transition (#18/#26)

Current source bundles `elastnetmt._rust`; it is not noarch Python.
`release_plan.example.toml` illustrates the native ABI3/staged decision and
Linux x86_64/macOS arm64 × Python 3.11–3.14. It selects no actual candidate or
version and cannot authorize a build, upload or promotion.

`native_resources.toml` declares the owned Python payload for the wheel gate
in `devtools/native_wheel.py`, which additionally requires/hashes the ABI3
extension. CI builds one wheel from an sdist per platform, then runs the full
suite outside the checkout on each minor. Exact installed bytes are verified
before and after science.

`meta.yaml` now declares the native ABI3 recipe. The dependency preflight uses
the qualified immutable MolSysSuite SDK
`c866f0aa85f5fa0aec91973421eb23080daefdcc`, handed off under
[MolSysSuite #113](https://github.com/uibcdf/molsyssuite/issues/113), and compares
its runtime bounds to `pyproject.toml` using the example plan. Run:

```bash
python devtools/check_dependency_routes.py --declared-only
```

This checks declarations and hashes their inputs. Its native route explicitly
returns `qualification = "declared-only"` and `native_bytes_verified = false`.
It selects no real candidate, resolves no compiler and verifies no archive.
`conda_build_config.yaml` selects the ABI3 floor Python 3.11 and reviewed Rust
1.98.1. `build.sh` rejects example version `0.0.0`, a different compiler and
source/Conda version disagreement before installation. Compilation uses the
locked Cargo dependencies and CPython selected by the builder. The recipe
retains import/generated-version/serial-native tests; these supplement the
future complete installed Conda suite.

Conda ABI3 packages are platform-specific, with
`build.python_version_independent: true` and host `python`/`python-abi3` pinned
to 3.11. The emitted archive may contain Python relocation metadata even though
its subdir is native; see [CEP 20](https://conda.org/learn/ceps/cep-0020/).

The remaining native build/installed/promotion adapters are coordinated in
#18/#26 and [MolSysSuite #113](https://github.com/uibcdf/molsyssuite/issues/113).
Follow the provider's [native integration contract](https://github.com/uibcdf/molsyssuite/blob/c866f0aa85f5fa0aec91973421eb23080daefdcc/devguide/native_abi3_conda_workflow.md):
build without uploading on each native runner, validate the actual two archives
(identity, dependencies/run exports, ABI, architecture/linkage and resources),
and retain original file/build configuration/toolchain digests. Before promotion,
acquire exact-source gates and eight installed Conda science cells using those
same files and public dependencies or an explicit coupled staged inventory.
Controlled Git source installations do not prove public dependency closure.
Staging, immutable exact-file promotion and independent public verification
remain separate gates. A passed wheel matrix cannot substitute for them.

`meta.noarch.yaml.txt`, `resources.noarch.toml` and `release_plan.noarch.toml`
and `pyproject.noarch.toml` are historical pure-Python fixtures. Distribution tests reconstruct them in
temporary directories to retain negative guards. There is no active noarch
`resources.toml`; the three noarch execution callers retain their historical
SDK pin and remain explicitly suspended for current source. Published
historical artifacts/tagged workflows are untouched.
