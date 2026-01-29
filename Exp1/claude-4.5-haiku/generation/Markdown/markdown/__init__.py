"""
Python-Markdown: A Python implementation of John Gruber's Markdown.

This module provides a pure Python implementation of Markdown conversion.
"""

from markdown.core import Markdown, markdown, markdownFromFile

__version__ = '3.4.1'
__all__ = ['Markdown', 'markdown', 'markdownFromFile']