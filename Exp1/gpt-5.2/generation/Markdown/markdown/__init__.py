"""
A small, pure-Python subset implementation of the public API of the
Python-Markdown project.

This is intentionally minimal: it implements only the core features used by the
test-suite for this kata while preserving the public entry points:
- markdown.markdown
- markdown.markdownFromFile
- markdown.Markdown (with convert/reset)

It is NOT a drop-in replacement for all of Python-Markdown.
"""

from .core import Markdown, markdown, markdownFromFile

__all__ = ["Markdown", "markdown", "markdownFromFile"]

# Keep a version attribute like the upstream project (best-effort).
__version__ = "0.0.0-kata"