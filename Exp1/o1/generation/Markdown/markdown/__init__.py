"""
markdown package: provides the top-level API for converting Markdown to HTML.
"""
from .core import Markdown, markdown, markdownFromFile

__all__ = ['Markdown', 'markdown', 'markdownFromFile']