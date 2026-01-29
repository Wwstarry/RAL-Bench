"""
Minimal, safe-to-evaluate subset of Fail2Ban.

This repository intentionally does NOT start daemons or modify firewall rules.
It provides a small API surface and offline regex/log matching utilities.
"""

__all__ = ["__version__"]
__version__ = "0.1.0"