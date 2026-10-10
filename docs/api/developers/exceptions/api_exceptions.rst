Exceptions
==========

Errors are exposed from the public ``elastnetmt`` namespace. Provider and
backend failures may propagate separately; cutoff optimization skips only
degenerate networks and constant theoretical B-factor profiles.

.. autoexception:: elastnetmt.ElastNetMTError

.. autoexception:: elastnetmt.ArgumentError

.. autoexception:: elastnetmt.InternalAlgorithmError

.. autoexception:: elastnetmt.DegenerateNetworkError

.. autoexception:: elastnetmt.InvalidSpectrumError

.. autoexception:: elastnetmt.UndefinedCorrelationError

.. autoexception:: elastnetmt.CutoffOptimizationError

.. autoexception:: elastnetmt.LibraryNotFoundError
