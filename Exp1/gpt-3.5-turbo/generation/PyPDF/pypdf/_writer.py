import io
from typing import Optional, Dict, Any, List, Union

from ._page import PageObject


class PdfWriter:
    def __init__(self):
        self._pages: List[PageObject] = []
        self._metadata: Optional[Dict[str, Any]] = None
        self._encrypt_password: Optional[str] = None

    def add_page(self, page: PageObject):
        # Add a page from a PdfReader
        self._pages.append(page)

    def add_blank_page(self, width: float = 612, height: float = 792):
        # Create a blank page dictionary
        page_dict = {
            b"/Type": b"/Page",
            b"/MediaBox": [0, 0, width, height],
            b"/Contents": b"",
            b"/Resources": {},
            b"/Rotate": 0,
        }
        page = PageObject(None, page_dict)
        self._pages.append(page)
        return page

    def add_metadata(self, info: Dict[str, Any]):
        self._metadata = info

    def encrypt(self, password: str):
        self._encrypt_password = password

    def write(self, stream: Union[io.IOBase, io.BytesIO]):
        # Write PDF to stream
        if not hasattr(stream, "write"):
            raise TypeError("stream must be a writable file-like object")

        # Build PDF objects
        objects = []
        obj_offsets = []
        obj_number = 1

        # Catalog object
        catalog_obj_num = obj_number
        obj_number += 1

        # Pages object
        pages_obj_num = obj_number
        obj_number += 1

        # Page objects
        page_obj_nums = []
        for _ in self._pages:
            page_obj_nums.append(obj_number)
            obj_number += 1

        # Info object (optional)
        info_obj_num = None
        if self._metadata:
            info_obj_num = obj_number
            obj_number += 1

        # Write header
        stream.write(b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n")

        # Write objects
        def write_obj(num: int, content: bytes):
            obj_offsets.append(stream.tell())
            stream.write(f"{num} 0 obj\n".encode("latin1"))
            stream.write(content)
            stream.write(b"\nendobj\n")

        # Write page objects
        for i, page in enumerate(self._pages):
            page_dict = page._dictionary.copy()
            # Fix /Parent to pages_obj_num
            page_dict[b"/Parent"] = pages_obj_num
            # Write page dictionary
            content = self._dict_to_pdf(page_dict)
            write_obj(page_obj_nums[i], content)

        # Write pages object
        kids_array = b"[ " + b" ".join(f"{n} 0 R".encode("latin1") for n in page_obj_nums) + b" ]"
        pages_dict = {
            b"/Type": b"/Pages",
            b"/Count": len(self._pages),
            b"/Kids": kids_array,
        }
        pages_content = self._dict_to_pdf(pages_dict)
        write_obj(pages_obj_num, pages_content)

        # Write catalog object
        catalog_dict = {
            b"/Type": b"/Catalog",
            b"/Pages": f"{pages_obj_num} 0 R".encode("latin1"),
        }
        catalog_content = self._dict_to_pdf(catalog_dict)
        write_obj(catalog_obj_num, catalog_content)

        # Write info object if any
        if self._metadata:
            info_dict = {}
            for k, v in self._metadata.items():
                key = k.encode("latin1") if isinstance(k, str) else k
                if isinstance(v, str):
                    val = f"({v})".encode("latin1")
                elif isinstance(v, int):
                    val = str(v).encode("latin1")
                else:
                    val = str(v).encode("latin1")
                info_dict[key] = val
            info_content = self._dict_to_pdf(info_dict)
            write_obj(info_obj_num, info_content)

        # Write xref table
        xref_start = stream.tell()
        stream.write(b"xref\n")
        stream.write(f"0 {obj_number}\n".encode("latin1"))
        stream.write(b"0000000000 65535 f \n")
        for offset in obj_offsets:
            stream.write(f"{offset:010} 00000 n \n".encode("latin1"))

        # Write trailer
        stream.write(b"trailer\n")
        trailer_dict = {
            b"/Size": obj_number,
            b"/Root": f"{catalog_obj_num} 0 R".encode("latin1"),
        }
        if info_obj_num:
            trailer_dict[b"/Info"] = f"{info_obj_num} 0 R".encode("latin1")
        if self._encrypt_password:
            # We do not implement real encryption, just mark encrypted
            trailer_dict[b"/Encrypt"] = b"<< /Filter /Standard /V 1 /R 2 >>"
        trailer_content = self._dict_to_pdf(trailer_dict)
        stream.write(trailer_content)
        stream.write(b"\nstartxref\n")
        stream.write(f"{xref_start}\n".encode("latin1"))
        stream.write(b"%%EOF\n")

    def _dict_to_pdf(self, d: dict) -> bytes:
        # Convert a dictionary to PDF dictionary syntax
        parts = [b"<<"]
        for k, v in d.items():
            if isinstance(k, str):
                k = k.encode("latin1")
            if isinstance(v, bytes):
                parts.append(k + b" " + v)
            elif isinstance(v, str):
                parts.append(k + b" (" + v.encode("latin1") + b")")
            elif isinstance(v, int):
                parts.append(k + b" " + str(v).encode("latin1"))
            elif isinstance(v, list):
                arr = b"[ " + b" ".join(self._pdf_value(x) for x in v) + b" ]"
                parts.append(k + b" " + arr)
            else:
                parts.append(k + b" " + self._pdf_value(v))
        parts.append(b">>")
        return b"\n".join(parts)

    def _pdf_value(self, v):
        if isinstance(v, bytes):
            return v
        elif isinstance(v, str):
            return b"(" + v.encode("latin1") + b")"
        elif isinstance(v, int):
            return str(v).encode("latin1")
        elif isinstance(v, list):
            return b"[ " + b" ".join(self._pdf_value(x) for x in v) + b" ]"
        else:
            return str(v).encode("latin1")