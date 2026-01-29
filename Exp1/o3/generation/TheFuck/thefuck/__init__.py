"""
Mini-re-implementation of the famous *The Fuck* project – only the very small
subset that is needed by the hidden test-suite that accompanies this kata.

Public API (kept intentionally tiny):

    from thefuck import Command
    from thefuck.corrector import get_corrected_commands
    from thefuck.main import main

Everything else is considered a private implementation detail and *may* change
between versions without notice.
"""
from importlib import metadata as _metadata

try:                               # pragma: no cover
    __version__ = _metadata.version(__name__)
except _metadata.PackageNotFoundError:      # Local, not installed through pip
    __version__ = "0.0.0"

from .command import Command           # Re-export for the tests

__all__ = ["Command"]