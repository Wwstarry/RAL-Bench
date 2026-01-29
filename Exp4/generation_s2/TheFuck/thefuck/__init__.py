"""A minimal, pure-Python reimplementation of core behaviors of The Fuck.

This repository is intended to satisfy a test suite that exercises a subset of
The Fuck's public API: CLI entry point, command representation, rule loading,
and suggestion generation.

The public API is intentionally small and stable.
"""

from .version import __version__  # noqa: F401