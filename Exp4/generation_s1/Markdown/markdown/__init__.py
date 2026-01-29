"""
A small, pure-Python Markdown-to-HTML library.

This package intentionally exposes a subset of the public API of the
reference Python-Markdown project sufficient for the bundled tests.
"""

from .core import Markdown, markdown, markdownFromFile

__all__ = ["Markdown", "markdown", "markdownFromFile"]
__version__ = "3.5.0-agent"