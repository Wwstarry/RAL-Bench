from .core import tabulate, simple_separated_format
from .formats import FORMATS, _table_formats

__all__ = ["tabulate", "simple_separated_format"] + list(_table_formats.keys())

# Expose preset formats as module-level constants
for fmt_name, fmt_func in _table_formats.items():
    globals()[fmt_name] = fmt_func