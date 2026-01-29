"""
Python-Markdown
===============

Python implementation of John Gruber's Markdown with a simple API.
"""

from .core import Markdown, markdown, markdownFromFile

__version__ = "1.0.0"

__all__ = ['Markdown', 'markdown', 'markdownFromFile']