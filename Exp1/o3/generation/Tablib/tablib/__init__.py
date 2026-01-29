"""
Lightweight, pure-Python subset implementation of the Tablib API required by
the test-suite.

This package purposefully implements only the portions that are exercised by
the tests.  It is NOT a full replacement for the real *tablib* library, but
should be good enough for most common, educational or small-scale workloads.
"""

from .core import Dataset, Databook        # noqa: F401

# Re-export helpers so `import tablib; tablib.Dataset` works.
__all__ = ["Dataset", "Databook"]