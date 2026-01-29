"""
Markdown-to-HTML conversion library.

This package provides a pure Python implementation of Markdown conversion
with an API compatible with the reference Python-Markdown project.
"""

from .core import markdown, markdownFromFile, Markdown

__all__ = ["markdown", "markdownFromFile", "Markdown"]