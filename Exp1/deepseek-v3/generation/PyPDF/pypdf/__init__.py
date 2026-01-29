"""
A pure Python PDF manipulation library API-compatible with pypdf.
"""

from ._reader import PdfReader
from ._writer import PdfWriter

__all__ = ["PdfReader", "PdfWriter"]