# Gaussian Network Model

```python
from elastnetmt import GaussianNetworkModel

gnm = GaussianNetworkModel("system.pdb", cutoff="7 angstroms", engine="vectorized")
scale, correlation = gnm.fit_to_experimental_b_factors()
b_factors = gnm.get_b_factors()  # magnitudes in square angstroms after fitting
gnm.show_b_factors()
```

The uncalibrated prediction is dimensionless. Fit it to experimental PDB B
factors before interpreting it in square angstroms. Repeating a fit preserves
the result; recalculating contacts resets the calibration. `n_modes` selects
the number of non-rigid modes, or `"all"` for the complete prediction.

`get_best_cutoff(min_cutoff="5 angstroms", max_cutoff="15 angstroms", steps=10)`
returns the cutoff and Pearson correlation and leaves the model fitted at that
cutoff. It skips disconnected candidates and constant theoretical profiles.
If the grid has no admissible candidate, it raises `CutoffOptimizationError`
and preserves the previous model state.

Predictions require at least two distinct nodes with finite coordinates and
a connected network. Fitting additionally requires experimental B factors
with one finite, nonnegative value per node and variation in both profiles.
Missing B factors still permit an uncalibrated prediction. Constant profiles
raise `UndefinedCorrelationError` because Pearson correlation is undefined.

Catch `DegenerateNetworkError` to revise the node selection or cutoff, or
`ArgumentError` to correct the input data. `InvalidSpectrumError` indicates a
numerical decomposition that violates the model contract and is propagated
by cutoff search. All scientific error types are exposed from `elastnetmt`.

```{eval-rst}
.. toctree::
   :maxdepth: 2

   Test_GNM.ipynb
```
