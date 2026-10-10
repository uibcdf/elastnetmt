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
`auto`, which uses the bundled serial Rust constructor with NumPy eigh.
`rust` requests the same backend explicitly; `vectorized` uses NumPy. Explicit
engines require their dependencies. Interpolation has its own engine argument
and defaults to `vectorized`. Physical spring stiffness calibration is not
implemented; keep `stiffness=None`.

Select at least three distinct nodes with finite coordinates. Vibrational
modes require a network with exactly six rigid zero modes; connectivity alone
does not guarantee sufficient geometric constraints. Collinear and other
underconstrained networks raise `DegenerateNetworkError` before caching a
result. Revise the selection or cutoff. A noncollinear three-node triangle is
supported. Invalid backend spectra raise `InvalidSpectrumError`.

```{eval-rst}
.. toctree::
   :maxdepth: 2

   Test_ANM.ipynb
```
