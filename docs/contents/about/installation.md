# Installation

The intended official public route is the UIBCDF Conda channel. At the 2026-10-06
review, the [official Conda API](https://api.anaconda.org/package/uibcdf/elastnetmt)
and [PyPI API](https://pypi.org/pypi/elastnetmt/json) returned HTTP 404. GitHub's
historical 0.1.0 release has no wheel/sdist assets. These are current bounded
observations; they do not establish that a package never existed.

Current source targets Python 3.11–3.14. The owned Rust construction backend requires a native
`cp311-abi3` extension. Current qualification builds platform wheels and tests
the same bytes outside source on Linux/macOS arm64 across all four minors.
The historical `noarch: python` Conda route is suspended; native Conda
preparation is coordinated through MolSysSuite #113.
A real committed release plan, executed candidate/installed gates, authorized
credentials and verified public poststate/clean installation remain prerequisites.
No current public installation command or Windows qualification is advertised here.

Follow [uibcdf/elastnetmt#18](https://github.com/uibcdf/elastnetmt/issues/18) for
distribution adoption and [uibcdf/elastnetmt#19](https://github.com/uibcdf/elastnetmt/issues/19)
for Python admission. Local `pip install --no-deps --editable .` after provisioning
the complete compatible Conda environment connects source to an interpreter;
Building from source requires Cargo/Rust and the build dependencies declared
in `pyproject.toml`. This does not certify public delivery or scientific correctness. Existing controlled
sibling Git routes remain source test evidence, with their shared preflight review
tracked in MolSysSuite #45.
