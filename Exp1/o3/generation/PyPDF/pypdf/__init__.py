"""
A *very* small, self-contained and **fake** replacement for the most commonly
used parts of the `pypdf` API needed by the test-suite that accompanies this
repository.

This implementation does **not** try to understand or generate real PDF
objects.  Instead it serialises a minimal JSON structure to bytes that *look*
like a PDF file (a fake header is included so that regular PDF viewers do not
break immediately).  All reading functionality is able to consume files
previously produced by :class:`pypdf.PdfWriter`.  It is **not** a general-
purpose PDF parser.

The goal is to satisfy the limited subset of functionality exercised by the
tests – reading / writing multi-page documents, basic page rotation, (fake)
encryption, and simple document metadata round-trips.

Public API re-exported at package level
---------------------------------------
from pypdf import PdfReader, PdfWriter, PageObject
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Union, IO, Sequence

from ._page import PageObject
from ._reader import PdfReader
from ._writer import PdfWriter

__all__ = [
    # public classes
    "PdfReader",
    "PdfWriter",
    "PageObject",
]

# Re-export important classes at top-level
PdfReader = PdfReader
PdfWriter = PdfWriter
PageObject = PageObject