"""
Very small stand-in for pypdf.PdfWriter.
"""
from __future__ import annotations

import io
from typing import Dict, List, Optional, Union, IO

from ._page import PageObject
from ._utils import dumps_doc


class PdfWriter:
    """
    A *very* small PDF writer that just serialises pages & metadata to a custom
    JSON structure intentionally disguised as a PDF file.
    """

    def __init__(self):
        self._pages: List[PageObject] = []
        self._metadata: Dict[str, str] = {}
        self._encrypt_password: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Page handling
    # ------------------------------------------------------------------ #
    def add_page(self, page: PageObject):
        if not isinstance(page, PageObject):
            raise TypeError("add_page expects a PageObject")
        self._pages.append(page)

    def add_blank_page(self, width: float = 612.0, height: float = 792.0) -> PageObject:
        page = PageObject(width=width, height=height, rotation=0)
        self.add_page(page)
        return page

    # ------------------------------------------------------------------ #
    # Metadata
    # ------------------------------------------------------------------ #
    def add_metadata(self, info: Dict[str, str]):
        if not isinstance(info, dict):
            raise TypeError("metadata must be a dict")
        # Store a shallow copy
        self._metadata.update({str(k): str(v) for k, v in info.items()})

    # ------------------------------------------------------------------ #
    # Encryption
    # ------------------------------------------------------------------ #
    def encrypt(self, password: str):
        # Real encryption would be here – we just remember the password.
        self._encrypt_password = str(password)

    # ------------------------------------------------------------------ #
    # Writing
    # ------------------------------------------------------------------ #
    def write(self, stream: Union[str, IO[bytes], io.BufferedIOBase]):
        """
        Serialise the current document into *stream*.

        *stream* may be:
          • a str / Path – interpreted as a file path to open,
          • a binary file-like object.
        """
        data = dumps_doc(
            {
                "pages": [p.to_dict() for p in self._pages],
                "metadata": self._metadata,
                "encrypted": self._encrypt_password is not None,
                "password": self._encrypt_password or "",
            }
        )

        if isinstance(stream, (str, bytes, io.PathLike)):
            with open(stream, "wb") as fp:
                fp.write(data)
        else:
            # assume file-like
            stream.write(data)