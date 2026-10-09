# Anisotropic Network Model

```python
from elastnetmt import AnisotropicNetworkModel

anm = AnisotropicNetworkModel("system.pdb", cutoff="12 angstroms", engine="vectorized")
trajectory = anm.trajectory_along_mode(
    mode=0, selection="all", amplitude="0.2 nm", oscillation_steps=20,
    interpolation_engine="vectorized",
)
```

`mode=0` selects the first non-rigid mode. The trajectory contains the requested
number of frames and selected atoms. Amplitude is a length specifying maximum
target atom displacement at the sine extrema; mode vectors themselves are
dimensionless. Equivalent length units produce equivalent trajectories.

The core engine accepts `vectorized`, `parallel` (Numba), `gpu` (CuPy), or
`auto`, which chooses Numba when available and otherwise NumPy. Explicit
engines require their dependencies. Interpolation has its own engine argument
and defaults to `vectorized`. Physical spring stiffness calibration is not
implemented; keep `stiffness=None`.

```{eval-rst}
.. toctree::
   :maxdepth: 2

   Test_ANM.ipynb
```
