"""
fail2ban.server namespace package – exposes two minimal modules:
    • filter
    • jail
"""
from importlib import import_module as _imp

__all__ = ["filter", "jail"]

def __getattr__(item):
    if item in __all__:
        return _imp(f"{__name__}.{item}")
    raise AttributeError(item)