"""
A **very** small subset re-implementation of the Mutagen package that is
sufficient for the unit–/performance–/resource–tests shipped with this
challenge.

Only the parts needed by the tests are provided – the *real* Mutagen package
is several orders of magnitude larger and more complete.
"""
from pathlib import Path
from typing import Any, List

# Public sub-modules – import lazily to avoid circular imports
from . import id3           # noqa – re-exported
from . import easyid3       # noqa – re-exported

__all__: List[str] = ["id3", "easyid3"]

# Convenience top-level re-exports (mirrors real mutagen)
EasyID3 = easyid3.EasyID3
ID3 = id3.ID3
version = "0.0.purepython"