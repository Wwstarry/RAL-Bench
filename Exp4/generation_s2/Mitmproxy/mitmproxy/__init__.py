"""
A minimal, safe-to-evaluate subset of mitmproxy.

This repository intentionally does not implement real proxying or interception.
It only provides a small API surface compatible with the unit tests for this kata.
"""

from __future__ import annotations

__all__ = [
    "__version__",
]

__version__ = "0.0.0"