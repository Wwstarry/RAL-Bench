from .core import tabulate, simple_separated_format
from .formats import PRESET_FORMATS as _PRESET_FORMATS

__all__ = ['tabulate', 'simple_separated_format']

# Expose preset formats as module-level variables
globals().update(_PRESET_FORMATS)
__all__.extend(_PRESET_FORMATS.keys())