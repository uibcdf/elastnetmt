# Building ElastNetMT documentation

Use the compatible suite development environment or the generated
`devtools/conda-envs/docs_env.yaml` environment, with ElastNetMT connected
to that interpreter. The environment provides Sphinx, MyST-NB and the PyData
theme. Public package delivery is tracked separately in #18/#19.

From the repository root:

```bash
OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLBACKEND=Agg python -m sphinx -n -W --keep-going -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` to review the result. A warning makes the
build fail. API pages import the public models and errors directly; the
publication workflow disables whole-repository sphinx-apidoc generation.

MyST-NB executes changed notebooks, fails on execution errors and runs kernels
in temporary working directories. The source notebooks contain no saved
outputs. Examples use MolSysMT's installed 1TCD PDB and vectorized CPU engines,
with assertions for array shapes, calibration and physical amplitude.
The cache lives under the ignored `docs/_build/.jupyter_cache` directory.
For an independent qualification, override `nb_execution_mode=force` and
`nb_execution_cache_path` to a task-owned temporary location; retain useful
HTML/log evidence while needed and clean temporary output afterward.

The legacy timestamp/in-place notebook executor and recursive API cleaner
were retired. Sphinx/MyST-NB owns execution, failure status and caching;
contributors do not need to rewrite notebooks or delete generated source trees.

The manual Documentation workflow publishes the strict build to gh-pages.
Inspect its result and verify the deployed ElastNetMT identity and repository
link before closing #13. A successful local build establishes source
documentation quality; it does not establish a deployed site or public
installed-package support.
