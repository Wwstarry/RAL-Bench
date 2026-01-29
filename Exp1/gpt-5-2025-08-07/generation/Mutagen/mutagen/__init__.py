"""
Minimal pure-Python tag-only implementation compatible with core interfaces of Mutagen
required by the test suite.

Provides:
- mutagen.easyid3.EasyID3
- mutagen.id3.ID3 and frame classes
"""

__all__ = ["easyid3", "id3"]

# Expose versions for compatibility; arbitrary static version string.
version = "0.0.0"