# Testing Strategy

ElastNetMT follows a Tiered testing protocol to ensure code integrity and physical correctness.

## Tier 1: Smoke Tests (Unit)
- **Purpose:** Ensure the library imports and basic objects are created without crashing.
- **Scope:** 
  - GNM/ANM initialization with small peptides.
  - Basic mathematical operations (matrix building).

## Tier 2: Physical Validation (Functional)
- **Purpose:** Verify that the results are physically sound.
- **Scope:**
  - Correlation of modeled B-factors vs experimental B-factors for the installed local TcTIM (1TCD) reference.
  - Verification that the first 6 eigenvalues in ANM are zero (within numerical tolerance).

## Tier 3: Integration Tests
- **Purpose:** Test the interoperability with other MolSysSuite tools.
- **Scope:**
  - Loading systems via `molsysmt`.
  - Visualizing networks in `molsysviewer`.

## Regression Tests
- **Purpose:** Ensure that bug fixes stay fixed.
- **Scope:** Any edge case found during development (e.g., systems with multiple chains, isolated residues).

---

To run tests:
```bash
python -m pytest --receptor=llm tests/
```
To check coverage:
```bash
python -m pytest --receptor=llm --cov=elastnetmt
```

Maintained CI uses `--receptor=ci` and pytest-receptor 1.2.1. Scientific
collection remains the complete `tests` directory. The test environments
include Numba so the accelerated parity test executes a real backend;
dependency-absence tests separately verify explicit failures and NumPy auto
selection. GPU execution requires suitable hardware and is not claimed by
the CPU matrix.

Reference tests resolve `molsysmt/data/pdb/1tcd.pdb` through installed package
resources. Small physical-contract tests use the deterministic eight-node
PDB fixture in `tests/conftest.py`; neither route downloads a PDB at runtime.

The optional-import architecture audit has one narrow adapter exemption:

```bash
depdigest audit --src-root elastnetmt --soft-deps numba,cupy,lindelint,nglview,sklearn \
  --exempt-file elastnetmt/_private/numba_kernels.py
```

This requested module imports Numba at module scope to define its decorated
kernels. It is imported only inside the Numba-guarded helpers in
`elastnetmt/_private/engines.py`; the package/model import paths never import
it. The exemption applies only to this file. Pair the syntax-only audit with
`tests/smoke/test_optional_engines.py`, which verifies additional imports in
a fresh process and explicit dependency/transitive-failure behavior.
