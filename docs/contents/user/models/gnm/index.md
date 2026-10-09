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
cutoff. Choose a range that keeps the selected network connected.

```{eval-rst}
.. toctree::
   :maxdepth: 2

   Test_GNM.ipynb
```
