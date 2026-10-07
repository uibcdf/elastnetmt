---
summary: Adopt the distribution policy and a guarded single-file noarch publication route.
issue: uibcdf/elastnetmt#18
status: partial
opened: 2026-10-01
closed:
verification: measured
area: [governance, distribution, compatibility]
guard: devtools/tests/test_distribution_contract.py
normative: MOLSYSSUITE_GUIDE.md
blocked_by: []
supersedes: []
---

# Noarch distribution adoption

## What

Adopt the suite distribution contract under uibcdf/molsyssuite#45. The maintainer
authorized adapting this publisher now and using `noarch: python`.

## How

The recipe declares one immutable noarch coordinate, preserves required metadata
constraints, uses host build tools and pip without dependency resolution. Thin
build/promotion wrappers reuse the common implementation at `a44e86a4f6a01dcbfe28fde46d886bc5cd4254c2`.
`devtools/conda-build/resources.toml` inventories the embedded version, package
roots and tracked runtime data. The example plan declares every supported source
CI job and its executed tests. A dedicated administrative reusable check inspects
the recipe/resources and publication controls without importing scientific code.

## Why

The old publisher used a moving action ref, interpreter/platform fan-out and
unrestricted manual public uploads. It did not retain the common exact-candidate
producer evidence. Its recipe did not declare noarch. The new route inspects the
exact built file before upload and promotes tested bytes without rebuilding.

## What is measured and what is assumed

Source inspection found pure Python code/data and no tracked bundled native
extension/executable. This migration is configuration and offline governance
work. It does not prove installed platform compatibility, scientific correctness,
credential access or public package availability. Full source CI remains unchanged;
internal direct/skip pushes remain available to dprada and LMMV.

## Alternatives and refuted paths

- A green recovery probe with skipped tests cannot authorize a candidate.
- Noarch does not prove macOS, Linux or Windows support.
- A second build/upload is not exact-file promotion.
- `release_plan.example.toml` does not authorize or select a public release.

## Scope and exclusions

Distribution governance and packaging identity/resources. Scientific algorithm
repairs and complete scientific execution belong to this component's team.

## Remaining adoption and acceptance criteria

- Review runtime environments/source routes against metadata with early negative
  dependency evidence and classify retained extra recipe requirements.
- Review each claimed public installation route without inferring it from config.
- Before a candidate, commit a reviewed actual release plan and immutable build.
- Execute the component-owned installed gate for the actual candidate before
  promotion. The current eight-cell descriptor retains the complete local suite
  and resource/launcher checks; missing, skipped or failed evidence fails closed.
- Confirm publication access only through an authorized maintainer.
- Register actual candidate/build/installed/public evidence only after execution.

The migration implements the common source route; whole-policy adoption remains
partial until these criteria are met. The common policy and module's negative
guards are the durable reference; the owning issue remains open.

## Administrative verification, 2026-10-01

The common early recipe/resource check passes with the example plan; the common
publication-control audit and actionlint pass for all three local wrappers.
Local reporting/index validation passes. No scientific module was imported for
these checks.

An isolated copy was prepared with the common static-version helper and
`pip wheel --no-deps --no-build-isolation`. The illustrative version was 0.0.0;
no release candidate or publication was selected. The wheel is `py3-none-any`,
contains all 4 declared paths and the matching embedded version. This
checks setuptools packaging only; it does not certify a Conda artifact, public
PyPI availability, installed resource use or any scientific/platform claim.

Central common implementation a44e86a passed native governance run 36898671705
and 249 local administrative tests. Its archive guards separately reject missing
resources, stale embedded versions and native payloads before upload.

The actual `elastnetmt/py.typed` resource was added to package-data; both the
core root and existing Viewer add-on root are inventoried and present.

## Installed qualification capability, 2026-10-01

The manual installed wrapper and committed six-cell descriptor are now delivered
through common 42e4de425871c125ef058842075c39e50fc6ac64. No installed scientific gate has been executed.
The workflow verifies the exact downloaded/installed Conda file and resources,
requires ordinary public dependency provenance and runs the whole local test
selection outside source, with import checks inside the pytest interpreter.
It neither uploads nor adds a scientific suite to internal pushes. The real
release plan and actual scientific/installed evidence remain future prerequisites.

## Maintained resource/publication checkpoint, 2026-10-06

The accepted shared SDK is now `38db709ecc07451ff36ea84573d585f9af6b4df7`
in all four publication wrappers. The resource inventory covers all thirty-six
tracked files in the core and Viewer add-on distribution roots, including private
diagnostics, add-on implementation and the version module. Inactive Python 2
legacy `model/old_anm.py` retains its existing owner issue `uibcdf/elastnetmt#12`;
this resource inventory does not make that path an advertised runtime feature.

The installed descriptor covers Linux/macOS arm64 Python 3.11–3.14 and now names
all four required provenance/science steps, including the post-test provenance
recheck. The optional promotion `qualification_sha` keeps a newer administrative
workflow distinct from the original producer SHA and exact artifact digest.
The onboarding example now includes twelve executed source jobs: eight full
source cells, independent governance, policy/lint/format, Conda governance and
the existing Viewer add-on contract. The real owner plan still needs an explicit
release decision; an example never authorizes a build or publication.

Nine independent administrative tests exercise the actual SDK against synthetic
archives: the complete payload passes; missing private/add-on resources, a stale
embedded version and an omitted required recipe dependency fail. The descriptor,
executed-gate declarations and original file/qualification identity are guarded.
These tests run only in the independent governance route under `devtools/tests`,
outside the unchanged complete scientific selection. The SDK checkout is excluded
from component lint discovery, preserving the source lint scope. No scientific
test, assertion, source pin or environment is changed at this checkpoint.

Read-only official public API inspection returned HTTP 404 for Conda and PyPI
package records. GitHub's 0.1.0 release has no distribution assets. This is bounded
public-route evidence, not a claim that a package never existed. Installation
guidance no longer advertises an unverified public Conda command. The prepared
noarch route, local source installation and actual public delivery are distinct.
The Python support badge remains tied to pending admission in #19.

### Remaining generic source-route decision

Current CI installs fixed Git revisions via `pip --no-deps`, with separate older-
minor/3.13/3.14 routes. Documentation uses public Conda; the existing add-on probe
deliberately follows current MolSysViewer development. The immutable source pins
and complete scientific commands are retained. Current metadata has ten required
runtime dependencies; this review invents no API floor and removes no requirement.

The shared dependency tool currently accepts only `pip-no-deps-directory`, requires
one source revision per provider and verifies installed directory provenance. It
cannot certify the existing VCS installation/context routes. Its ordinary runtime
channel profile also does not model the currently retained ambermd extension.
Source preflight adoption must address those inputs explicitly; the declarations
and archive tests above are not a passing whole-route dependency audit.

The principal maintainer is reviewing whether to extend that shared tool for the
existing immutable VCS routes or migrate the source-install transport to reviewed
local checkouts. The recommended shared extension checks declared repository/full
commit, installed VCS provenance and actual version against metadata, binds the
selected Python/environment context and rejects moving refs for qualified routes.
It distinguishes a declaration-only check from actual installed qualification.
Controlled Conda bootstrap/source overlays and additional channels need explicit
reviewed purposes; no missing/weak required constraint can be excused by a reason.
The current-development Viewer probe stays separately classified until its evidence
can support an immutable release candidate. Owning provider need: uibcdf/molsyssuite#107;
central adoption coordination remains uibcdf/molsyssuite#45.

No first release, real artifact, credentials, installed scientific matrix, promotion,
clean public install or complete source-route adoption is claimed. This review
remains partial. Scientific failures remain with #14/#17/#19 and this component's
team; MolSysMT/MolSysViewer full scientific suites and active clones are preserved.

## Immutable Git/context adoption — 2026-10-07

Principal maintainer accepted preserving transport and adding the shared general
profile in uibcdf/molsyssuite#107. Accepted immutable SDK
`2d32048457c6d37093ae509f5626d00a5cda121b` passes native governance
37578744225 with 394 central tests; sixty-five focused provider guards and an
isolated real pip Git provenance probe pass. All wrappers and the independent
SDK test checkout use this accepted pin; no new Action release is adopted.

`devtools/dependency_routes.toml` inventories eighteen recipe/environment/workflow
routes, thirteen source records, both unchanged actual Git manifests and seven
contexts. Existing Python-specific commits and scientific steps, triggers and
recovery are preserved. Runtime declarations add missing direct requirements and
supported Python bounds without scientific API floors; actual fixed Git source
providers stay separate from reviewed Conda bootstrap overlaps. AmberMD remains
an explicit scientific channel extension in the specialized environments.

`devtools/check_dependency_routes.py` delegates to the accepted shared operation.
Independent governance reviews declarations and runs seven owner source-route
negative guards. Before every original source science job, it checks the selected
actual interpreter, versions and PEP 610 Git repository/commit provenance. Checker
libraries are installed into `.molsyssuite-tools`, visible only to the checker
process; they do not replace scientific environment libraries. Candidate plans
require the executed source preflight step as well as the complete tests.

Local checks pass nine existing archive/publication tests, seven new source-route
tests, three reporting tests, Ruff over 62 files, format and workflow lint.
Declaration evidence is not actual installed qualification. Native source-context
results follow at the pushed owner commit; failed science still belongs to the
component team. Source-free production/development/docs actual checks, legacy
broadcaster/helper controls, full successful release gates, real plan/access,
original installed artifact and independent public qualification remain pending.
Whole adoption and CI/recipe stay partial, access unknown. No package is built,
staged, replaced, promoted or publicly qualified by these source controls.
