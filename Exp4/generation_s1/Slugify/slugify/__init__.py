"""
Lightweight, pure-Python slugification compatible with the core API of
the `python-slugify` project as exercised by the benchmark tests.

Public API:
    from slugify import slugify
    from slugify.slugify import slugify
"""

from .slugify import slugify

__all__ = ["slugify"]
__version__ = "0.0.0"