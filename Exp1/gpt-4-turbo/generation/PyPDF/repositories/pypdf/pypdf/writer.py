import io
import time
from .generic import DictionaryObject, ArrayObject, NameObject, NumberObject, TextStringObject, encode_pdf_string
from .page import PageObject

class PdfWriter:
    def __init__(self):
        self._pages = []
        self._objects = []
        self._metadata = {}
        self._encrypt = None
        self._id_counter = 1
        self._obj_map = {}
        self._root_objnum = None

    def add_page(self, page):
        # Accepts a PageObject
        self._pages.append(page)

    def add_blank_page(self, width=612, height=792):
        # Create a blank page
        page_dict = DictionaryObject()
        page_dict["/Type"] = "/Page"
        page_dict["/MediaBox"] = ArrayObject([0, 0, width, height])
        page_dict["/Contents"] = None
        page_dict["/Resources"] = DictionaryObject()
        page_obj = PageObject(None, page_dict, index=len(self._pages))
        self.add_page(page_obj)
        return page_obj

    def add_metadata(self, mapping):
        for k, v in mapping.items():
            self._metadata[k] = v

    def encrypt(self, password):
        # For pure Python, just mark as encrypted
        self._encrypt = password

    def write(self, file_obj):
        # Write PDF to file_obj
        obj_offsets = []
        obj_data = []
        objnum_map = {}
        objnum = 1

        # Catalog
        catalog = DictionaryObject()
        catalog["/Type"] = "/Catalog"
        # Pages tree
        pages_dict = DictionaryObject()
        pages_dict["/Type"] = "/Pages"
        pages_dict["/Count"] = len(self._pages)
        pages_dict["/Kids"] = ArrayObject()
        # Write page objects
        page_objnums = []
        for page in self._pages:
            page_dict = DictionaryObject()
            for k, v in page.page_dict.items():
                page_dict[k] = v
            page_dict["/Parent"] = None  # Will be set later
            page_objnums.append(objnum)
            objnum_map[id(page)] = objnum
            obj_data.append((objnum, 0, page_dict))
            objnum += 1
        # Now set /Kids
        pages_dict["/Kids"] = ArrayObject([f"{n} 0 R" for n in page_objnums])
        obj_data.append((objnum, 0, pages_dict))
        pages_objnum = objnum
        objnum += 1
        # Catalog points to pages
        catalog["/Pages"] = f"{pages_objnum} 0 R"
        obj_data.append((objnum, 0, catalog))
        catalog_objnum = objnum
        objnum += 1
        # Info
        if self._metadata:
            info_dict = DictionaryObject()
            for k, v in self._metadata.items():
                info_dict[k] = v
            obj_data.append((objnum, 0, info_dict))
            info_objnum = objnum
            objnum += 1
        else:
            info_objnum = None
        # Encrypt
        if self._encrypt:
            encrypt_dict = DictionaryObject()
            encrypt_dict["/Filter"] = "/Standard"
            encrypt_dict["/V"] = 1
            encrypt_dict["/R"] = 2
            encrypt_dict["/O"] = encode_pdf_string(self._encrypt)
            encrypt_dict["/U"] = encode_pdf_string(self._encrypt)
            encrypt_dict["/P"] = -4
            obj_data.append((objnum, 0, encrypt_dict))
            encrypt_objnum = objnum
            objnum += 1
        else:
            encrypt_objnum = None

        # Write header
        file_obj.write(b"%PDF-1.4\n")
        # Write objects
        offsets = []
        for objnum_, gennum_, obj in obj_data:
            offsets.append(file_obj.tell())
            file_obj.write(f"{objnum_} {gennum_} obj\n".encode())
            self._write_object(obj, file_obj)
            file_obj.write(b"\nendobj\n")
        # Write xref
        xref_offset = file_obj.tell()
        file_obj.write(b"xref\n")
        file_obj.write(f"0 {len(obj_data)+1}\n".encode())
        file_obj.write(b"0000000000 65535 f \n")
        for off in offsets:
            file_obj.write(f"{off:010d} 00000 n \n".encode())
        # Write trailer
        file_obj.write(b"trailer\n")
        trailer_dict = DictionaryObject()
        trailer_dict["/Size"] = len(obj_data)+1
        trailer_dict["/Root"] = f"{catalog_objnum} 0 R"
        if info_objnum:
            trailer_dict["/Info"] = f"{info_objnum} 0 R"
        if encrypt_objnum:
            trailer_dict["/Encrypt"] = f"{encrypt_objnum} 0 R"
        self._write_object(trailer_dict, file_obj)
        file_obj.write(b"\nstartxref\n")
        file_obj.write(f"{xref_offset}\n".encode())
        file_obj.write(b"%%EOF\n")

    def _write_object(self, obj, file_obj):
        if isinstance(obj, DictionaryObject):
            file_obj.write(b"<<\n")
            for k, v in obj.items():
                file_obj.write(f"{k} ".encode())
                self._write_object(v, file_obj)
                file_obj.write(b"\n")
            file_obj.write(b">>")
        elif isinstance(obj, ArrayObject):
            file_obj.write(b"[ ")
            for v in obj:
                self._write_object(v, file_obj)
                file_obj.write(b" ")
            file_obj.write(b"]")
        elif isinstance(obj, str):
            if re.match(r"\d+ \d+ R", obj):
                file_obj.write(obj.encode())
            elif obj.startswith("/"):
                file_obj.write(obj.encode())
            else:
                file_obj.write(f"({obj})".encode())
        elif isinstance(obj, (int, float)):
            file_obj.write(str(obj).encode())
        elif obj is None:
            file_obj.write(b"null")
        elif isinstance(obj, bytes):
            file_obj.write(b"<")
            file_obj.write(obj.hex().encode())
            file_obj.write(b">")
        else:
            file_obj.write(str(obj).encode())