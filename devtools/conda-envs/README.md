# Owner Conda environment tools

Owning review: uibcdf/elastnetmt#18; shared dependency ranges and provenance:
uibcdf/molsyssuite#107. These helpers manage development environments. They
neither qualify a release nor publish a package.

## Inputs and generation

`pyproject.toml` owns required runtime dependencies and Python bounds.
`devtools/requirements.yaml` owns ordinary environment tooling. The default test
file derives its fixed-source omissions and PyUnitWizard/MolSysMT bootstrap overlays from
`devtools/dependency_routes.toml`; the actual immutable Git inputs remain separate.

From any working directory:

```bash
ELASTNETMT_SUITE_ROOT=/path/to/accepted/sdk python /path/to/elastnetmt/devtools/broadcast_requirements.py --check
# Regenerate all six ordinary environment files after reviewing metadata/tools:
ELASTNETMT_SUITE_ROOT=/path/to/accepted/sdk python /path/to/elastnetmt/devtools/broadcast_requirements.py
```

Generation validates every document before writing. Check mode rejects drift
without mutation. The recipe, release plan, source manifests and specialized
3.13/3.14/importable environment files are outside its write scope. Recipe
changes retain their separate review and shared preflight; raw Jinja is never
loaded and dumped as ordinary YAML.

## Create and update

Use a Python interpreter with `PyYAML` and `packaging`, plus a clean MolSysSuite
SDK at `c866f0aa85f5fa0aec91973421eb23080daefdcc`. Point
`ELASTNETMT_SUITE_ROOT` to that SDK, or use the reviewed `.molsyssuite` checkout.
It is not installed into the scientific environment. Existing isolated checker
libraries under `.molsyssuite-tools` are visible only to the helper process.

```bash
python devtools/conda-envs/create_conda_env.py -n elastnetmt-dev -p 3.14 devtools/conda-envs/development_env.yaml
conda activate elastnetmt-dev
python devtools/conda-envs/update_conda_env.py devtools/conda-envs/development_env.yaml
```

Creation requires a new environment name and defaults to Python 3.14. Updates
target the executing interpreter's active Conda prefix with `--prune`; review
that manifest before removing unlisted packages. Both operations use strict
channel priority, an argument vector and checked exit status. Temporary YAML
is cleaned on success or failure, with no working-directory or source-file
mutation. `MAMBA_EXE`/`CONDA_EXE` or the executable search path select the manager;
Mamba does not require a second Conda executable.

The whole selected minor must fit both project metadata and the input Python
selector. Existing patch/build restrictions need explicit review rather than
silent widening. Routine development requires 3.14. Fixed-source environment
selection follows its recorded contexts: the ordinary test file is for 3.11/3.12,
the specialized files for 3.13 and 3.14 respectively. Creating an environment
does not install those Git providers; execute the reviewed source route and
actual context preflight separately before scientific tests.

## Administrative verification

```bash
ELASTNETMT_SUITE_ROOT=/path/to/accepted/sdk python -m unittest discover -s devtools/tests -p test_environment_tools.py
```

The independent governance job checks generated inputs and runs these guards.
The tests simulate Conda; they do not mutate an actual environment. Source-free
production/development/docs installation evidence and exact-candidate scientific
and installed-package gates remain separate prerequisites under #18.
