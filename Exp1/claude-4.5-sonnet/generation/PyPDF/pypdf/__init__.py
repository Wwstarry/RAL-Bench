"""
Pure Python PDF manipulation library - API-compatible with pypdf.
"""

from pypdf.reader import PdfReader
from pypdf.writer import PdfWriter
from pypdf.page import PageObject

__all__ = ['PdfReader', 'PdfWriter', 'PageObject']