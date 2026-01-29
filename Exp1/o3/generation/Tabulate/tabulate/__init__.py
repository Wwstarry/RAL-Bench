"""
A tiny re-implementation of the most frequently used parts of
the ``tabulate`` project (https://github.com/astanin/python-tabulate).

Only a subset of the original public API is implemented – just
enough for the vast majority of run-time, documentation and test-
suite use-cases that rely on the real *tabulate* package.

The implementation purposefully lives in pure Python and tries
to stay dependency–free.
"""

from .core import tabulate, simple_separated_format
from .formats import TABLE_FORMATS as _TABLE_FORMATS

__all__ = [
    "tabulate",
    "simple_separated_format",
    "TABLE_FORMATS",
]

# preset formats re-exported for convenience – exactly like the
# reference implementation does
TABLE_FORMATS = _TABLE_FORMATS
for _name, _ in TABLE_FORMATS.items():
    globals()[_name] = _name  # allow ``tabulate.plain`` style access