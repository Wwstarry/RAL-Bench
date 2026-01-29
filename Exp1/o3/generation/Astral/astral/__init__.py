"""
A very small subset re-implementation of the excellent `astral` package
covering only the functionality required by the accompanying test-suite.

Implemented parts
-----------------
* LocationInfo – basic container for a geographical location
* Observer     – latitude / longitude / elevation container
* astral.sun   – sunrise / sunset helpers + umbrella `sun()` function
* astral.moon  – simple moon‐phase calculator

All calculations are performed with pure Python code and the standard
library, there are **no external runtime dependencies**.

Accuracy
--------
The algorithms implemented here are based on the NOAA Solar Calculator
for sunrise/sunset and on a simple synodic month model for lunar phase.
The results are sufficiently accurate (usually within 1-2 minutes of the
reference Astral package) and are stable and monotonic between days.
"""
from __future__ import annotations

# Re-export the public API so it can be used via `import astral`
from .location import LocationInfo, Observer

# Sub-modules
from . import sun as sun        # noqa: F401 – re-export as a submodule
from . import moon as moon      # noqa: F401 – re-export as a submodule

__all__ = ["LocationInfo", "Observer", "sun", "moon"]