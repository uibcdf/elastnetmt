import time

import numpy as np
import pytest

from elastnetmt import AnisotropicNetworkModel


@pytest.mark.smoke
def test_anm_benchmark_engines():
    """
    Compare Vectorized vs Parallel (Numba) engines for ANM.
    """
    pdb_id = "pdb_id:1tcd"

    # 1. Vectorized Engine
    anm_vec = AnisotropicNetworkModel(
        pdb_id, selection='atom_name=="CA"', engine="vectorized"
    )
    t0 = time.time()
    e_vec = anm_vec.get_eigenvalues(include_rigid_modes=True)
    t_vec = time.time() - t0

    # 2. Parallel Engine (Numba)
    anm_par = AnisotropicNetworkModel(
        pdb_id, selection='atom_name=="CA"', engine="parallel"
    )
    # Warmup
    anm_par.get_eigenvalues()

    t0 = time.time()
    anm_par._reset_spectral_results()  # Clear cache to re-trigger solve
    e_par = anm_par.get_eigenvalues(include_rigid_modes=True)
    t_par = time.time() - t0

    print(f"\n[ANM Benchmark] Nodes: {anm_vec.n_nodes}")
    print(f"Vectorized Time: {t_vec:.4f}s")
    print(f"Parallel Time:   {t_par:.4f}s")
    print(f"Speedup:         {t_vec / t_par:.1f}x")

    # Parity check
    np.testing.assert_allclose(e_vec, e_par, atol=1e-10)
