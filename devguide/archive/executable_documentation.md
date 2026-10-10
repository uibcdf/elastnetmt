---
summary: Repair the public API reference, navigation and executable tutorials.
issue: uibcdf/elastnetmt#25
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: measured
area: [documentation, validation]
guard: tests/documentation/test_public_examples.py
normative: docs/README.md
blocked_by: []
supersedes: []
---

# Executable documentation and API ownership

## What

At d07537d, a clean Sphinx build aborts while importing
molsysmt._private.exceptions.NotImplementedMethodError from a copied API page.
Navigation targets nonexistent quickstart, tools and cookbook pages.
Tutorials use openenm/enmt imports, unavailable view_mode/show_* methods and
remote PDB input. The homepage advertises an unqualified installation and
conflicting version/support/citation metadata.

## How

Document the public ENM/GNM/ANM classes in NumPy style (#8) and expose their
owned public errors in the API reference. Repair internal navigation, replace
stale source tutorials with local MolSysMT 1TCD CPU examples and assert model
shapes, calibration, eigenpair properties and physical trajectory amplitude.
Use MyST-NB execution/cache/temp-CWD operations through a strict Sphinx build.
Disable whole-repository sphinx-apidoc generation in the publication workflow.
Retire the unreferenced timestamp/in-place executor and recursive API cleaner.

## Why

Readers must be able to reproduce the documented computation and understand
its units, mode ordering and actionable failures. A copied API or saved widget
output cannot establish current public behavior.

## What is measured and what is assumed

The original HTML build failed during autosummary initialization before it
could check navigation. Three public class-example tests pass on Python 3.14.7
after correction. Complete strict notebook/HTML qualification is recorded
after execution. Jupyter kernel startup needs local sockets; the sandbox
rejected them, so execution uses the explicitly approved unrestricted route
with task-owned IPython, Matplotlib and temporary directories.

## Alternatives and refuted paths

Suppressing Sphinx warnings or disabling notebook execution leaves the broken
contracts untested. Shared molecular parsing and interpolation remain with
their providers. No new custom notebook cache or API generator is needed.

## Scope and exclusions

Source documentation and public model docstrings. Deployed identity remains
#13 until the published site is verified; public installed delivery is #18/#19.
The Rust study is #26 and is not an implemented engine. The temporary-resource
evidence covers this task's build/kernel resources, not the full #24 audit.

## Acceptance criteria

A strict HTML build executes the numerical tutorials and returns success with
zero warnings. Internal navigation and owned API objects resolve. Public
docstring examples execute without network acquisition. No unavailable model
operation or unqualified installation/support claim remains in the tutorials.

## Resolution, 2026-10-10

The corrected strict Sphinx 9.1.0/MyST-NB 1.4.0 HTML build passes with
`-n -W --keep-going`, a fresh doctree/cache and forced notebook execution
on Python 3.14.7. All eight source notebooks are processed, including the
five numerical tutorials. There are no Sphinx warnings or notebook failures.
Jupyter emits its own local TCP transport notices; these are not Sphinx
reference or execution warnings and were not suppressed. HTML/log output
is retained under ignored docs/_build for review. The full local suite
passes 130 tests, including the three new runnable public-example guards.
Ruff passes and the executable ASTs of the three changed models match the
previous source; only their documentation changed.

Provider types/defaults render through Napoleon's type preprocessing;
external types are literal so the build does not require remote inventories.
Shapes remain in the descriptions. Deployment (#13) and public artifacts
(#18/#19) are separate uncompleted acceptance boundaries.
