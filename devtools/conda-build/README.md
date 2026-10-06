# elastnetmt Conda publication

Owning review: uibcdf/elastnetmt#18; suite contract: uibcdf/molsyssuite#45.

This recipe now produces one `noarch: python` file. Its Python bounds and required
runtime dependencies follow `pyproject.toml`; no Python 3.7 or per-platform
conversion route is used. Build tools are host requirements. The shared workflow
freezes the reviewed version in an ephemeral checkout and inspects metadata,
embedded version and the committed resource inventory before uploading.

Follow the [shared noarch workflow guide](https://github.com/uibcdf/molsyssuite/blob/main/devguide/noarch_conda_workflow.md).
All four publication wrappers pin MolSysSuite at `38db709ecc07451ff36ea84573d585f9af6b4df7`.
The existing `ANACONDA_UIBCDF_TOKEN` secret is explicitly mapped; its availability
and validity have not been confirmed by this migration.

`release_plan.example.toml` is an example only. Before the first affected release,
review and commit `release_plan.toml` with a real immutable version/build and
candidate conditions. The example declares twelve executed jobs: all eight source
cells, independent governance, policy/lint/format, Conda governance and the existing
Viewer add-on contract. A green daily probe with omitted science is insufficient.
The dependency-route audit is still pending the shared VCS/context decision under
uibcdf/molsyssuite#45; resource declarations alone do not qualify the runtime.

The first noarch candidate must be staged, then qualified outside the source
checkout across every claimed OS/Python cell. The component-owned installed wrapper now calls the shared
qualification workflow across the committed eight-cell Linux/macOS arm64 matrix
(Python 3.11–3.14). Every cell requires installation, file validation, scientific
tests and the post-science provenance recheck to execute successfully.
Its `installed_tests` selection retains the whole local `tests` directory.
Dispatch it explicitly for the staged filename/digest; it never runs on pushes.
Failed/missing/skipped installed evidence blocks promotion. Run-title/file/digest
binding and descriptor fields are defined in the shared guide.

Dispatch the build wrapper with full candidate SHA and reviewed version. Dispatch
promotion with that SHA, version, staged digest and existing successful installed
run ID. An optional newer `qualification_sha` names the installed workflow separately
from the original producer/file/digest. Promotion adds a label to the same tested file; it does not build or upload
again. Later direct releases need an eligible reviewed plan, exact-tag CI evidence,
public dependency closure and conclusive all-label absence. Never overwrite.

This configuration is administrative readiness only. No scientific execution,
installed OS claim, credential check, source tag or package publication occurred.
Remaining dependency-environment/public-claim review stays in the owning issue.

The inventory covers all thirty-six tracked core/add-on files; it does not certify
scientific feature behavior or the legacy inactive Python 2 path under #12.
Nine administrative tests exercise actual SDK resource/archive/descriptor checks:

```bash
ELASTNETMT_SUITE_ROOT=/path/to/reviewed/molsyssuite python -m unittest discover -s devtools/tests -p test_distribution_contract.py
```

The public Conda/PyPI APIs returned 404 at the 2026-10-06 review and GitHub's
historical release has no distribution assets. No current public installation is
inferred. Retain the source pins, scientific selection and dependency environments
until the shared source-route design is accepted and independently qualified.
