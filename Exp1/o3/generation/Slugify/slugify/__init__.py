"""
A very small subset implementation of the ``python-slugify`` package
interface that is **just good enough** for the educational test-suite
shipped with this repository.

Public API
----------
slugify.slugify          -> main slugification helper

Nothing else should be relied upon from the outside world.
"""
from __future__ import annotations

from .slugify import slugify  # noqa: F401 – re-export convenience