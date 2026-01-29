"""
A small, pure-Python subset implementation compatible with the core API of
the reference `python-slugify` project as used by this kata's tests.
"""

from .slugify import slugify

__all__ = ["slugify"]