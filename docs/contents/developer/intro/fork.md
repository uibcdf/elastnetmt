# Source checkout and contribution routes

Clone the canonical repository:

```bash
git clone https://github.com/uibcdf/elastnetmt.git
cd elastnetmt
```

Provision a compatible development environment before connecting this source:

```bash
python -m pip install --no-deps --editable .
```

This command does not install the dependency environment or qualify public
delivery. Follow the suite's maintained environment recipe and the
[local environment guidance](https://github.com/uibcdf/elastnetmt/tree/main/devtools).

External contributions use branches and pull requests with the required
checks. Authorized internal maintainer work may use direct commits and
pushes under the suite checkpoint policy. Keep focused changes and run checks
appropriate to their scope; authorization is specific to the maintainer/task.

Documentation contributors should use the strict build described in
[docs/README.md](https://github.com/uibcdf/elastnetmt/blob/main/docs/README.md).
