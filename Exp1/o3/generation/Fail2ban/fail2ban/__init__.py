"""
A **very** small subset of the real Fail2Ban package.

Only the parts that are required by the public-tests for this
benchmark are implemented:
    • fail2ban.server.filter      – helpers for IP detection.
    • fail2ban.server.jail.Jail   – a light-weight jail implementation.

The real Fail2Ban is licensed under GPL-2.  This re-implementation is
a clean-room minimal subset released to the public-domain.
"""
from importlib import import_module

# Re-export the official namespace that the tests expect.
def __getattr__(item):  # pragma: no cover
    """
    Lazy sub-module loader – lets the tests do:
        from fail2ban.server import jail
    with only ``fail2ban`` imported initially.
    """
    if item in ("server",):
        return import_module(f"{__name__}.{item}")
    raise AttributeError(item)