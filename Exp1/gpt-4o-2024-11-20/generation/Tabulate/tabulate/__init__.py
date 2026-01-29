# tabulate/__init__.py

from .core import tabulate
from .formats import simple_separated_format, PRESET_FORMATS

__all__ = ["tabulate", "simple_separated_format"] + list(PRESET_FORMATS.keys())