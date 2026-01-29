"""
A minimal, safe-to-evaluate subset of the mitmproxy package.

This repository intentionally does not implement real interception/MITM features.
It only provides a compatible module layout and small API surface for tests.
"""

__all__ = ["http", "flow", "addonmanager"]
__version__ = "0.0.0"