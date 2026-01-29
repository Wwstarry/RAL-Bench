"""
This is a pure Python implementation of the tabulate library,
API-compatible with the core features of the original.
"""

__all__ = [
    "tabulate",
    "simple_separated_format",
]
__version__ = "0.9.0"

from .core import tabulate, simple_separated_format
from .formats import _table_formats

# Expose table formats as top-level variables in this module
for fmt_name in _table_formats:
    globals()[fmt_name] = fmt_name
    if fmt_name not in __all__:
        __all__.append(fmt_name)

# Add common aliases for formats
if "github" not in globals():
    globals()["github"] = "pipe"
    __all__.append("github")
if "markdown" not in globals():
    globals()["markdown"] = "pipe"
    __all__.append("markdown")