"""
A tiny, pure-Python subset of the Mutagen API required by the test suite.

This is NOT the real Mutagen project. It implements only:
- mutagen.easyid3.EasyID3
- mutagen.id3.ID3 and a few frame classes (TIT2, TPE1, COMM, APIC)

It persists tags in a simple custom container embedded in files (including
tag-only ".mp3" files), sufficient for roundtripping within this library.
"""

from __future__ import annotations

__all__ = ["easyid3", "id3", "__version__"]
__version__ = "0.0.0"

# Ensure submodules are importable as in the reference project
from . import easyid3 as easyid3  # noqa: F401
from . import id3 as id3  # noqa: F401