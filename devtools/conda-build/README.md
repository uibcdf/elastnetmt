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

Native Conda recipe/build/installed/promotion adapters remain coordinated in
[MolSysSuite #113](https://github.com/uibcdf/molsyssuite/issues/113). The inspected
immutable SDK cannot audit native recipes; its noarch adapters reject native
files. Adopt a qualified immutable native profile or reviewed equivalent before
activating a recipe or selecting a real decision. Candidate/installed science,
staging, immutable exact-file promotion and independent public verification
remain the suite contract.

`meta.noarch.yaml.txt`, `resources.noarch.toml` and `release_plan.noarch.toml`
and `pyproject.noarch.toml` are historical pure-Python fixtures. Distribution tests reconstruct them in
temporary directories to retain negative guards. There is no active `meta.yaml`
or `resources.toml`; the three noarch execution callers are explicitly suspended
for current source. Published historical artifacts/tagged workflows are untouched.
