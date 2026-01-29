"""
A small, pure-Python Markdown-to-HTML converter exposing a subset of the
Python-Markdown public API.

This module is intentionally minimal but API-compatible (for core usage) with
the reference `markdown` project for the purposes of the accompanying tests.
"""

from .core import Markdown, markdown, markdownFromFile

__all__ = ["Markdown", "markdown", "markdownFromFile"]

__version__ = "0.0.test"