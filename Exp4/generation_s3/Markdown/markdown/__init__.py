"""
A small, pure-Python Markdown-to-HTML converter providing a subset of the
Python-Markdown public API.

This is intended to be API-compatible with the core entry points used by tests:
- markdown.markdown(text, **kwargs)
- markdown.markdownFromFile(**kwargs)
- markdown.Markdown class with convert(text) and reset()
"""

from __future__ import annotations

from .core import Markdown, markdown, markdownFromFile

__all__ = [
    "Markdown",
    "markdown",
    "markdownFromFile",
]

# Version metadata (tests may look for these in some environments)
__version__ = "3.0.0-pure"
version = __version__
version_info = (3, 0, 0)