"""
A tiny pure-Python subset of the Mutagen API required by the benchmark tests.

This is NOT a real ID3 implementation. It provides a stable round-trippable
storage format for ID3-like metadata with an API compatible with a small subset
of Mutagen used by the test suite.
"""

from .easyid3 import EasyID3
from .id3 import ID3, TIT2, TPE1, COMM, APIC

__all__ = ["EasyID3", "ID3", "TIT2", "TPE1", "COMM", "APIC"]
__version__ = "0.0.0-agent"