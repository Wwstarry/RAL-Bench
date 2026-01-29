"""
A minimal, safe-to-evaluate subset of the mitmproxy package.

This repository is intentionally non-functional as a proxy: it only provides
a small API surface for importability and CLI argument parsing tests.
"""

from __future__ import annotations

__all__ = [
    "__version__",
]

__version__ = "0.0.0"