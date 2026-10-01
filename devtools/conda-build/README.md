# elastnetmt Conda publication

Owning review: uibcdf/elastnetmt#18; suite contract: uibcdf/molsyssuite#45.

This recipe now produces one `noarch: python` file. Its Python bounds and required
runtime dependencies follow `pyproject.toml`; no Python 3.7 or per-platform
conversion route is used. Build tools are host requirements. The shared workflow
freezes the reviewed version in an ephemeral checkout and inspects metadata,
embedded version and the committed resource inventory before uploading.

Follow the [shared noarch workflow guide](https://github.com/uibcdf/molsyssuite/blob/main/devguide/noarch_conda_workflow.md).
The thin build and promotion wrappers pin MolSysSuite at `42e4de425871c125ef058842075c39e50fc6ac64`.
The existing `ANACONDA_UIBCDF_TOKEN` secret is explicitly mapped; its availability
and validity have not been confirmed by this migration.

`release_plan.example.toml` is an example only. Before the first affected release,
review and commit `release_plan.toml` with a real immutable version/build and
candidate conditions. Require every declared source CI cell and its executed
`Run tests` step. A green daily probe with omitted science is insufficient.

The first noarch candidate must be staged, then qualified outside the source
checkout across every claimed OS/Python cell. The component-owned installed wrapper now calls the shared
qualification workflow across the committed six-cell Linux/macOS arm64 matrix.
Its `installed_tests` selection retains the whole local `tests` directory.
Dispatch it explicitly for the staged filename/digest; it never runs on pushes.
Failed/missing/skipped installed evidence blocks promotion. Run-title/file/digest
binding and descriptor fields are defined in the shared guide.

Dispatch the build wrapper with full candidate SHA and reviewed version. Dispatch
promotion with that SHA, version, staged digest and existing successful installed
run ID. Promotion adds a label to the same tested file; it does not build or upload
again. Later direct releases need an eligible reviewed plan, exact-tag CI evidence,
public dependency closure and conclusive all-label absence. Never overwrite.

This configuration is administrative readiness only. No scientific execution,
installed OS claim, credential check, source tag or package publication occurred.
Remaining dependency-environment/public-claim review stays in the owning issue.
