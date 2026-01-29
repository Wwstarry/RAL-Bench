"""
Python-Markdown
===============

A Python implementation of John Gruber's Markdown.

This is a pure Python library that is API-compatible with the core
functionality of the reference Python-Markdown library.

Basic Usage:

    >>> import markdown
    >>> text = "Some *markdown* text."
    >>> html = markdown.markdown(text)
    >>> print(html)
    <p>Some <em>markdown</em> text.</p>

For more information, see the official Python-Markdown documentation.
"""

from .core import Markdown, markdown, markdownFromFile

__all__ = ['Markdown', 'markdown', 'markdownFromFile']