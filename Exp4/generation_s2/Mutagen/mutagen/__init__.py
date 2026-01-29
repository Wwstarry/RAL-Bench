"""
A tiny, pure-Python subset of the Mutagen API required by the test suite.

This is NOT a full implementation of the real mutagen project. It implements:
- mutagen.easyid3.EasyID3 (mapping-like interface)
- mutagen.id3.ID3 and a few frame types (TIT2, TPE1, COMM, APIC)

Files written are "tag-only MP3" stubs: an ID3v2 header followed by serialized
frames, with no MPEG audio frames required by the tests.
"""

from __future__ import annotations

__all__ = ["easyid3", "id3", "EasyID3", "ID3"]

from .easyid3 import EasyID3  # noqa: E402
from .id3 import ID3  # noqa: E402

__version__ = "0.0.teststub"