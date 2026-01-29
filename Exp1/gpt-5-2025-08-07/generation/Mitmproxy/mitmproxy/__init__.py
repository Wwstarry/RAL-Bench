"""
Minimal, safe-to-evaluate subset of mitmproxy.

This package provides a very small portion of mitmproxy's public API surface so
that other projects can import modules and symbols, construct parsers, and run
basic orchestration code without performing any network operations.
"""

__all__ = ["__version__"]

# A synthetic version string to satisfy --version CLI output and tests.
__version__ = "0.0.0-synthetic"