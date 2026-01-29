"""
Implements the PdfWriter class for pypdf.
Provides add_page, add_blank_page, write, encrypt, add_metadata.
"""

import io
import time

from ._page import PageObject

class PdfWriter:
    """
    Creates a new PDF file in memory from pages added or created, with optional encryption.
    """

    def __init__(self):
        # List of PageObjects
        self._pages = []
        # Metadata dictionary for Info
        self._metadata = {}
        # Encryption state
        self._encrypt_user_password = None
        self._encrypt_key = None

    def add_page(self, page):
        """
        Add a page (PageObject) to the PDF.
        """
        if not isinstance(page, PageObject):
            raise ValueError("add_page requires a PageObject.")
        self._pages.append(page)

    def add_blank_page(self, width=612, height=792):
        """
        Adds a blank page with the specified dimensions.
        """
        new_page = PageObject(mediabox=[0, 0, width, height], contents=b"", rotation=0)
        self._pages.append(new_page)
        return new_page

    def encrypt(self, user_password, owner_password=None, use_128bit=True):
        """
        Set up encryption for this PDF. For this naive implementation,
        we store the user password and pretend to generate a key.
        """
        if not user_password:
            raise ValueError("User password cannot be empty for encryption.")
        self._encrypt_user_password = user_password
        # We'll pretend we derive an encryption key. This is not production safe.
        self._encrypt_key = b"FAKE_KEY_FOR_" + user_password.encode("utf-8")

    def add_metadata(self, info_dict):
        """
        Add document metadata. info_dict keys like "/Title", "/Author", etc.
        """
        for k, v in info_dict.items():
            self._metadata[k] = v

    def write(self, stream):
        """
        Write the PDF data to the provided file-like object or filename.
        If encryption was enabled, we embed a naive /Encrypt dictionary 
        and do not do real RC4/AES encryption on the content (for demonstration).
        """
        output = self._build_pdf()
        if isinstance(stream, str):
            with open(stream, "wb") as f:
                f.write(output)
        else:
            stream.write(output)

    def _build_pdf(self):
        """
        Build a minimal PDF file in memory, returning its bytes.
        """
        # We'll produce a naive PDF with the following objects:
        # 1: Catalog
        # 2: Pages
        # 3..(3+N-1): Each page
        # +1 Info dictionary
        # If encrypted, add an /Encrypt object
        # This is extremely simplified.

        # PDF Header
        parts = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]

        obj_index = 1
        # Catalog object
        catalog_id = obj_index; obj_index += 1
        # Pages object
        pages_id = obj_index; obj_index += 1
        page_ids = []

        # Page objects
        for _ in self._pages:
            page_ids.append(obj_index)
            obj_index += 1

        # Info dictionary
        info_id = obj_index; obj_index += 1

        # Possibly encryption object
        encrypt_id = None
        if self._encrypt_user_password:
            encrypt_id = obj_index
            obj_index += 1

        # Construct catalog
        catalog_obj = self._obj_to_pdf(
            catalog_id,
            {
                b"Type": b"Catalog",
                b"Pages": f"{pages_id[0] - 1} 0 R".encode("ascii")  # pages object reference
            }
        )

        # Construct pages object
        kids_str = b"[ " + b" ".join(f"{pid} 0 R".encode("ascii") for pid in page_ids) + b" ]"
        pages_obj = self._obj_to_pdf(
            pages_id,
            {
                b"Type": b"Pages",
                b"Count": str(len(self._pages)).encode("ascii"),
                b"Kids": kids_str
            }
        )

        # Page objects
        page_objs = []
        for i, page in enumerate(self._pages):
            contents_id = obj_index
            obj_index += 1
            # Build the page dictionary
            page_dict = {
                b"Type": b"Page",
                b"Parent": f"{pages_id} 0 R".encode("ascii"),
                b"MediaBox": f"[0 0 {page.mediabox[2]} {page.mediabox[3]}]".encode("ascii"),
                b"Rotate": str(page.rotation).encode("ascii"),
                b"Contents": f"{contents_id} 0 R".encode("ascii"),
            }
            page_objs.append(self._obj_to_pdf(page_ids[i], page_dict))

            # Build the contents object
            page_stream_data = page.contents
            if self._encrypt_key:
                # If encryption is on, we'd do real encryption. We'll skip and store the same.
                pass
            content_obj = self._stream_obj_to_pdf(contents_id, page_stream_data)
            page_objs.append(content_obj)

        # Info dictionary
        info_dict = {}
        for k, v in self._metadata.items():
            if not k.startswith("/"):
                # Guarantee leading slash
                k = "/" + k
            info_dict[k.encode("ascii")] = f"({v})".encode("latin-1", "ignore")

        info_obj = self._obj_to_pdf(info_id, info_dict)

        # Encryption object if needed
        encrypt_obj = b""
        if encrypt_id:
            # We add a naive encryption dictionary
            encrypt_obj = self._obj_to_pdf(
                encrypt_id,
                {
                    b"Filter": b"/Standard",
                    b"V": b"2",
                    b"R": b"3",
                    b"O": b"(FAKE_OWNER)",
                    b"U": b"(FAKE_USER)",
                    b"P": b"-3904",  # huge negative int
                }
            )

        # Gather all objects
        xrefs = []
        offset = 0
        # We have these objects in order:
        objects = [
            catalog_obj,
            pages_obj,
        ]
        objects.extend(page_objs)
        objects.append(info_obj)
        if encrypt_obj:
            objects.append(encrypt_obj)

        # Build each object, record offset
        full_body = b""
        index = 1
        for obj_data in objects:
            xrefs.append(offset)
            full_body += obj_data
            offset = len(full_body)
            index += 1

        # Now build the xref table and trailer
        # total objects = len(objects)
        total_objects = len(xrefs)
        xref_start = len(full_body)
        xref_table = [b"xref\n"]
        xref_table.append(f"0 {total_objects+1}\n".encode("ascii"))
        # xref for obj 0
        xref_table.append(b"0000000000 65535 f \n")
        for off in xrefs:
            xref_table.append(f"{off:010d} 00000 n \n".encode("ascii"))

        xref_block = b"".join(xref_table)

        full_body += xref_block

        # trailer
        trailer_dict = {
            b"Size": str(total_objects+1).encode("ascii"),
            b"Root": f"{1} 0 R".encode("ascii"),
            b"Info": f"{total_objects} 0 R".encode("ascii"),  # info is last non-encrypt if no encryption
        }
        if encrypt_id:
            # Put encryption ref in the trailer
            trailer_dict[b"Encrypt"] = f"{total_objects} 0 R".encode("ascii")
            # Then adjusting Info to be total_objects - 1?
            trailer_dict[b"Info"] = f"{total_objects-1} 0 R".encode("ascii")

        trailer_str = b"trailer\n<<"
        for k, v in trailer_dict.items():
            trailer_str += b"/" + k + b" " + v + b"\n"
        # ID array
        trailer_str += b"/ID [<0123456789ABCDEF> <0123456789ABCDEF>]\n"
        trailer_str += b">>\n"

        full_body += trailer_str
        full_body += f"startxref\n{xref_start}\n%%EOF\n".encode("ascii")

        parts.append(full_body)
        return b"".join(parts)

    def _obj_to_pdf(self, obj_id, dictionary):
        """
        Build an indirect object from a Python dictionary, returning its PDF bytes.
        dictionary is a mapping of PDF keys to raw PDF-encoded bytes values
        e.g. { b'Type': b'/Catalog', b'Pages': b'2 0 R' }
        """
        body = f"{obj_id} 0 obj\n<<".encode("ascii")
        for k, v in dictionary.items():
            body += b"\n" + b"/" + k + b" " + v
        body += b"\n>>\nendobj\n"
        return body

    def _stream_obj_to_pdf(self, obj_id, data):
        """
        Build an indirect stream object from data bytes.
        """
        header = f"{obj_id} 0 obj\n<< /Length {len(data)} >>\nstream\n".encode("ascii")
        footer = b"\nendstream\nendobj\n"
        return header + data + footer