"""
Light-weight, pure-Python replacement for the most commonly-used public API of
`python-dateutil`.  Only the subset of functionality required by the
test-suite is implemented.

Provided sub-modules:
    - dateutil.parser
    - dateutil.relativedelta
    - dateutil.rrule
    - dateutil.tz
"""

from importlib import import_module
import sys
from types import ModuleType

# Make sub-packages importable at ``dateutil.xxx``
_submodules = ("parser", "relativedelta", "rrule", "tz")
_this_module = sys.modules[__name__]

for _name in _submodules:
    _module = import_module(f"{__name__}.{_name}")
    setattr(_this_module, _name, _module)

__all__ = list(_submodules)