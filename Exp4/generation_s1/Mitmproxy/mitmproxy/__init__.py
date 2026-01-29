"""
A minimal, safe-to-evaluate subset of mitmproxy.

This package intentionally does not implement any networking or MITM behavior.
It only provides a small API surface and CLI skeleton used by the test suite.
"""
from .version import __version__

__all__ = ["__version__"]