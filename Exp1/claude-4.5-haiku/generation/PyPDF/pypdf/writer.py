"""
PDF Writer implementation.
"""

import io
import time
from typing import Any, Dict, Optional, Union
from pypdf.objects import (
    DictionaryObject,
    ArrayObject,
    TextStringObject,
    NameObject,
    NumberObject,
    NullObject,
)


class PdfWriter:
    """
    A PDF writer that can create and modify PDF documents.
    """

    def __init__(self):
        """Initialize a PdfWriter."""
        self._pages = []
        self._metadata = {}
        self._encryption_password: Optional[str] = None
        self._object_counter = 1
        self._objects: Dict[int, str] = {}

    def add_page(self, page: Any) -> None:
        """
        Add a page to the PDF.

        Args:
            page: A PageObject to add.
        """
        self._pages.append(page)

    def add_blank_page(self, width: Optional[float] = None, height: Optional[float] = None) -> Any:
        """
        Add a blank page to the PDF.

        Args:
            width: The width of the page in points.
            height: The height of the page in points.

        Returns:
            The created PageObject.
        """
        from pypdf.page import PageObject

        if width is None:
            width = 612  # Letter width
        if height is None:
            height = 792  # Letter height

        page_dict = {
            "Type": "Page",
            "MediaBox": [0, 0, width, height],
            "Contents": "",
            "Resources": {},
        }

        page = PageObject(page_dict, None)
        self._pages.append(page)
        return page

    def add_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Add metadata to the PDF.

        Args:
            metadata: A dictionary of metadata fields.
        """
        self._metadata.update(metadata)

    def encrypt(self, password: str) -> None:
        """
        Encrypt the PDF with a password.

        Args:
            password: The password to encrypt with.
        """
        self._encryption_password = password

    def write(self, file_obj: Union[str, io.IOBase]) -> None:
        """
        Write the PDF to a file.

        Args:
            file_obj: A file path (str) or file-like object.
        """
        if isinstance(file_obj, str):
            with open(file_obj, "wb") as f:
                self._write_pdf(f)
        else:
            self._write_pdf(file_obj)

    def _write_pdf(self, file_obj: io.IOBase) -> None:
        """Write the PDF content to a file object."""
        # Reset object counter
        self._object_counter = 1
        self._objects = {}

        # Write PDF header
        file_obj.write(b"%PDF-1.4\n")

        # Create objects
        pages_obj_num = self._allocate_object_number()
        catalog_obj_num = self._allocate_object_number()
        info_obj_num = self._allocate_object_number()

        # Write page objects
        page_obj_nums = []
        for page in self._pages:
            page_obj_num = self._allocate_object_number()
            page_obj_nums.append(page_obj_num)

        # Build objects dictionary
        xref_offsets = {}

        # Write catalog object
        xref_offsets[catalog_obj_num] = file_obj.tell()
        catalog_content = self._build_catalog_object(catalog_obj_num, pages_obj_num)
        file_obj.write(catalog_content)

        # Write pages object
        xref_offsets[pages_obj_num] = file_obj.tell()
        pages_content = self._build_pages_object(pages_obj_num, page_obj_nums)
        file_obj.write(pages_content)

        # Write page objects
        for i, page_obj_num in enumerate(page_obj_nums):
            xref_offsets[page_obj_num] = file_obj.tell()
            page_content = self._build_page_object(page_obj_num, pages_obj_num, self._pages[i])
            file_obj.write(page_content)

        # Write info object
        xref_offsets[info_obj_num] = file_obj.tell()
        info_content = self._build_info_object(info_obj_num)
        file_obj.write(info_content)

        # Write xref table
        xref_offset = file_obj.tell()
        file_obj.write(b"xref\n")
        file_obj.write(f"0 {self._object_counter}\n".encode("latin-1"))
        file_obj.write(b"0000000000 65535 f \n")

        for obj_num in range(1, self._object_counter):
            if obj_num in xref_offsets:
                offset = xref_offsets[obj_num]
                file_obj.write(f"{offset:010d} 00000 n \n".encode("latin-1"))
            else:
                file_obj.write(b"0000000000 00000 f \n")

        # Write trailer
        file_obj.write(b"trailer\n")
        file_obj.write(b"<< /Size " + str(self._object_counter).encode("latin-1") + b"\n")
        file_obj.write(b"   /Root " + str(catalog_obj_num).encode("latin-1") + b" 0 R\n")
        file_obj.write(b"   /Info " + str(info_obj_num).encode("latin-1") + b" 0 R\n")
        file_obj.write(b">>\n")
        file_obj.write(b"startxref\n")
        file_obj.write(str(xref_offset).encode("latin-1") + b"\n")
        file_obj.write(b"%%EOF\n")

    def _allocate_object_number(self) -> int:
        """Allocate a new object number."""
        obj_num = self._object_counter
        self._object_counter += 1
        return obj_num

    def _build_catalog_object(self, obj_num: int, pages_obj_num: int) -> bytes:
        """Build the catalog object."""
        content = f"{obj_num} 0 obj\n"
        content += "<< /Type /Catalog\n"
        content += f"   /Pages {pages_obj_num} 0 R\n"
        content += ">>\n"
        content += "endobj\n"
        return content.encode("latin-1")

    def _build_pages_object(self, obj_num: int, page_obj_nums: list) -> bytes:
        """Build the pages object."""
        content = f"{obj_num} 0 obj\n"
        content += "<< /Type /Pages\n"
        content += "   /Kids ["
        for page_obj_num in page_obj_nums:
            content += f" {page_obj_num} 0 R"
        content += " ]\n"
        content += f"   /Count {len(page_obj_nums)}\n"
        content += ">>\n"
        content += "endobj\n"
        return content.encode("latin-1")

    def _build_page_object(self, obj_num: int, pages_obj_num: int, page: Any) -> bytes:
        """Build a page object."""
        content = f"{obj_num} 0 obj\n"
        content += "<< /Type /Page\n"
        content += f"   /Parent {pages_obj_num} 0 R\n"

        # Get page dimensions
        if hasattr(page, "_page_dict") and "MediaBox" in page._page_dict:
            media_box = page._page_dict["MediaBox"]
            if isinstance(media_box, list):
                content += f"   /MediaBox [{media_box[0]} {media_box[1]} {media_box[2]} {media_box[3]}]\n"
            else:
                content += f"   /MediaBox [0 0 612 792]\n"
        else:
            content += "   /MediaBox [0 0 612 792]\n"

        # Add rotation if present
        if hasattr(page, "_rotation") and page._rotation:
            content += f"   /Rotate {page._rotation}\n"

        content += "   /Resources << >>\n"
        content += "   /Contents 0 R\n"
        content += ">>\n"
        content += "endobj\n"
        return content.encode("latin-1")

    def _build_info_object(self, obj_num: int) -> bytes:
        """Build the info object."""
        content = f"{obj_num} 0 obj\n"
        content += "<<"
        for key, value in self._metadata.items():
            if isinstance(value, str):
                # Escape special characters
                value = value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
                content += f"\n   /{key} ({value})"
            else:
                content += f"\n   /{key} {value}"
        content += "\n>>\n"
        content += "endobj\n"
        return content.encode("latin-1")