"""
Pure Python PDF manipulation library.
API-compatible with pypdf.
"""

from ._reader import PdfReader
from ._writer import PdfWriter
from ._page import PageObject

__all__ = ["PdfReader", "PdfWriter", "PageObject"]