"""
Minimal, pure-Python implementation of core behavior of The Fuck.

This package is intentionally small but keeps the public API surface that tests
expect: rule discovery, Command representation, suggestions, and CLI entrypoint.
"""

from .version import __version__  # noqa: F401
from .types import Command  # noqa: F401
from .corrector import get_corrected_commands  # noqa: F401