# NumPy-style docstrings

ElastNetMT documents its public model classes and methods in NumPy style.
The [API reference](../../../../api/index.md) is generated from those
docstrings, including constructor parameters.

Document parameter defaults, selection/index mappings, return shapes and
units, and the scientific errors a caller can handle. State when quantities
are normalized: GNM raw fluctuations and eigenvectors are dimensionless,
while calibrated B-factor magnitudes are in square angstroms.

Use runnable examples with installed local data and explicit CPU engines.
Examples should assert stable properties rather than a backend-dependent
eigenvector sign or a fixed timing. Do not advertise reserved rendering or
stiffness parameters as implemented functionality.

See the maintained [documentation standards](https://github.com/uibcdf/elastnetmt/blob/main/devguide/documentation_standards.md).
