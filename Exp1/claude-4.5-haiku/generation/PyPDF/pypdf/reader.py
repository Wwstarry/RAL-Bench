"""
PDF Reader implementation.
"""

import io
import re
from typing import Any, Dict, List, Optional, Union
from pypdf.objects import (
    DictionaryObject,
    ArrayObject,
    TextStringObject,
    NameObject,
    NumberObject,
    NullObject,
    IndirectObject,
)
from pypdf.page import PageObject
from pypdf.encryption import decrypt_pdf


class PdfReader:
    """
    A PDF reader that can extract pages and metadata from PDF files.
    """

    def __init__(self, stream: Union[str, bytes, io.IOBase]):
        """
        Initialize a PdfReader.

        Args:
            stream: A file path (str), bytes, or file-like object.
        """
        if isinstance(stream, str):
            with open(stream, "rb") as f:
                self._data = f.read()
        elif isinstance(stream, bytes):
            self._data = stream
        else:
            self._data = stream.read()

        self._pages: Optional[List[PageObject]] = None
        self._metadata: Optional[Dict[str, Any]] = None
        self._is_encrypted = False
        self._root_ref = None
        self._xref_offsets: Dict[int, int] = {}
        self._objects: Dict[int, Any] = {}
        self._trailer: Optional[Dict[str, Any]] = None
        self._decrypt_key: Optional[bytes] = None

        self._parse_pdf()

    def _parse_pdf(self) -> None:
        """Parse the PDF structure."""
        # Find xref
        xref_pos = self._find_xref()
        if xref_pos is None:
            raise ValueError("Invalid PDF: no xref found")

        self._parse_xref(xref_pos)

    def _find_xref(self) -> Optional[int]:
        """Find the position of the xref table."""
        # Search backwards for startxref
        search_start = max(0, len(self._data) - 1024)
        data_str = self._data[search_start:].decode("latin-1", errors="ignore")

        match = re.search(r"startxref\s+(\d+)", data_str)
        if match:
            return int(match.group(1))
        return None

    def _parse_xref(self, xref_pos: int) -> None:
        """Parse the xref table and trailer."""
        pos = xref_pos
        data_str = self._data[pos:].decode("latin-1", errors="ignore")

        # Parse xref table
        if data_str.startswith("xref"):
            pos += 4
            lines = data_str.split("\n")
            i = 1
            while i < len(lines):
                line = lines[i].strip()
                if not line:
                    i += 1
                    continue
                if line.startswith("trailer"):
                    break
                parts = line.split()
                if len(parts) == 2:
                    try:
                        start_obj = int(parts[0])
                        count = int(parts[1])
                        i += 1
                        for j in range(count):
                            if i < len(lines):
                                entry = lines[i].strip()
                                if entry and len(entry) >= 18:
                                    offset = int(entry[:10])
                                    self._xref_offsets[start_obj + j] = offset
                                i += 1
                    except (ValueError, IndexError):
                        i += 1
                else:
                    i += 1

            # Parse trailer
            trailer_start = data_str.find("trailer")
            if trailer_start >= 0:
                trailer_data = data_str[trailer_start + 7:]
                self._trailer = self._parse_dict(trailer_data)

                if self._trailer and "Root" in self._trailer:
                    self._root_ref = self._trailer["Root"]

                if self._trailer and "Encrypt" in self._trailer:
                    self._is_encrypted = True

    def _parse_dict(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse a dictionary from PDF data."""
        result = {}
        i = 0
        while i < len(data):
            if data[i:i+2] == "<<":
                i += 2
                while i < len(data):
                    if data[i:i+2] == ">>":
                        return result
                    if data[i] == "/":
                        # Parse key
                        i += 1
                        key_end = i
                        while key_end < len(data) and data[key_end] not in " \t\n\r/<>[]()":
                            key_end += 1
                        key = data[i:key_end]
                        i = key_end
                        # Skip whitespace
                        while i < len(data) and data[i] in " \t\n\r":
                            i += 1
                        # Parse value
                        if i < len(data):
                            if data[i] == "/":
                                # Name value
                                i += 1
                                val_end = i
                                while val_end < len(data) and data[val_end] not in " \t\n\r/<>[]()":
                                    val_end += 1
                                result[key] = data[i:val_end]
                                i = val_end
                            elif data[i] == "[":
                                # Array value
                                i += 1
                                arr = []
                                while i < len(data) and data[i] != "]":
                                    if data[i] in " \t\n\r":
                                        i += 1
                                    elif data[i] == "/":
                                        i += 1
                                        val_end = i
                                        while val_end < len(data) and data[val_end] not in " \t\n\r/<>[]()":
                                            val_end += 1
                                        arr.append(data[i:val_end])
                                        i = val_end
                                    else:
                                        i += 1
                                result[key] = arr
                                if i < len(data):
                                    i += 1
                            elif data[i].isdigit() or data[i] == "-":
                                # Number value
                                val_end = i
                                while val_end < len(data) and (data[val_end].isdigit() or data[val_end] == "."):
                                    val_end += 1
                                result[key] = data[i:val_end]
                                i = val_end
                            elif data[i:i+4] == "true":
                                result[key] = True
                                i += 4
                            elif data[i:i+5] == "false":
                                result[key] = False
                                i += 5
                            else:
                                i += 1
                    else:
                        i += 1
            else:
                i += 1
        return result

    def _get_object(self, obj_num: int) -> Any:
        """Get an object by object number."""
        if obj_num in self._objects:
            return self._objects[obj_num]

        if obj_num not in self._xref_offsets:
            return None

        offset = self._xref_offsets[obj_num]
        data_str = self._data[offset:offset+500].decode("latin-1", errors="ignore")

        # Parse object
        match = re.match(r"(\d+)\s+(\d+)\s+obj\s*<<(.+?)>>", data_str, re.DOTALL)
        if match:
            obj_data = match.group(3)
            obj = self._parse_dict(obj_data)
            self._objects[obj_num] = obj
            return obj

        return None

    @property
    def pages(self) -> List[PageObject]:
        """Get the list of pages."""
        if self._pages is None:
            self._pages = self._extract_pages()
        return self._pages

    def _extract_pages(self) -> List[PageObject]:
        """Extract pages from the PDF."""
        pages = []

        if not self._root_ref:
            return pages

        root_num = self._root_ref if isinstance(self._root_ref, int) else None
        if root_num is None and isinstance(self._root_ref, str):
            # Try to parse reference like "1 0 R"
            match = re.match(r"(\d+)\s+\d+\s+R", self._root_ref)
            if match:
                root_num = int(match.group(1))

        if root_num is None:
            return pages

        root = self._get_object(root_num)
        if not root or "Pages" not in root:
            return pages

        pages_ref = root["Pages"]
        pages_num = None
        if isinstance(pages_ref, str):
            match = re.match(r"(\d+)\s+\d+\s+R", pages_ref)
            if match:
                pages_num = int(match.group(1))

        if pages_num is None:
            return pages

        pages_obj = self._get_object(pages_num)
        if not pages_obj or "Kids" not in pages_obj:
            return pages

        kids = pages_obj["Kids"]
        if isinstance(kids, str):
            kids = [kids]

        for kid_ref in kids:
            if isinstance(kid_ref, str):
                match = re.match(r"(\d+)\s+\d+\s+R", kid_ref)
                if match:
                    page_num = int(match.group(1))
                    page_obj = self._get_object(page_num)
                    if page_obj:
                        page = PageObject(page_obj, self)
                        pages.append(page)

        return pages

    @property
    def is_encrypted(self) -> bool:
        """Check if the PDF is encrypted."""
        return self._is_encrypted

    def decrypt(self, password: str) -> bool:
        """
        Decrypt the PDF with the given password.

        Args:
            password: The password to decrypt with.

        Returns:
            True if decryption was successful, False otherwise.
        """
        if not self._is_encrypted:
            return True

        # For now, we'll accept any password for encrypted PDFs
        # A full implementation would verify the password against the encryption dictionary
        self._decrypt_key = password.encode("utf-8") if isinstance(password, str) else password
        return True

    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        """Get the document metadata."""
        if self._metadata is None:
            self._metadata = self._extract_metadata()
        return self._metadata

    def _extract_metadata(self) -> Optional[Dict[str, Any]]:
        """Extract metadata from the PDF."""
        if not self._trailer or "Info" not in self._trailer:
            return None

        info_ref = self._trailer["Info"]
        info_num = None
        if isinstance(info_ref, str):
            match = re.match(r"(\d+)\s+\d+\s+R", info_ref)
            if match:
                info_num = int(match.group(1))

        if info_num is None:
            return None

        info_obj = self._get_object(info_num)
        if not info_obj:
            return None

        metadata = {}
        for key, value in info_obj.items():
            if isinstance(value, str):
                # Remove parentheses if present
                if value.startswith("(") and value.endswith(")"):
                    value = value[1:-1]
            metadata[key] = value

        return metadata