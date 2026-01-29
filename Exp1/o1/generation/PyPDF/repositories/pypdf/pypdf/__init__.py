"""
pypdf package: provides PdfReader and PdfWriter classes
"""

from ._reader import PdfReader
from ._writer import PdfWriter

__all__ = ["PdfReader", "PdfWriter"]