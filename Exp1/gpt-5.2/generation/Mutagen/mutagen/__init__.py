"""
A tiny, pure-Python subset of the Mutagen API sufficient for the unit tests.

This is *not* a full ID3 implementation. It stores tags in a small, deterministic
binary container embedded in the target file, and supports a minimal Mutagen-like
API surface for EasyID3 and ID3 frame operations.
"""

from __future__ import annotations

from .easyid3 import EasyID3  # noqa: F401
from .id3 import ID3, TIT2, TPE1, COMM, APIC  # noqa: F401

__all__ = ["EasyID3", "ID3", "TIT2", "TPE1", "COMM", "APIC"]

__version__ = "0.0.test"