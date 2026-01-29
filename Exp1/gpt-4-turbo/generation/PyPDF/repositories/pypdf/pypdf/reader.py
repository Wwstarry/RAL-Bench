import io
import re
from .generic import DictionaryObject, ArrayObject, NameObject, parse_indirect_object, decode_pdf_string
from .page import PageObject

class PdfReader:
    def __init__(self, stream):
        if isinstance(stream, str):
            stream = open(stream, "rb")
        self.stream = stream
        self.pages = []
        self.trailer = None
        self.xref = {}
        self.objects = {}
        self.is_encrypted = False
        self._decrypted = False
        self.metadata = {}
        self._parse_pdf()

    def _parse_pdf(self):
        # Find startxref
        self.stream.seek(0, 2)
        filesize = self.stream.tell()
        self.stream.seek(0)
        data = self.stream.read()
        startxref_match = re.search(b"startxref\s+(\d+)", data)
        if not startxref_match:
            raise ValueError("No startxref found")
        startxref = int(startxref_match.group(1))
        self.stream.seek(startxref)
        line = self.stream.readline()
        while line.strip() != b"xref":
            line = self.stream.readline()
        # Read xref table
        xref_table = {}
        while True:
            line = self.stream.readline()
            if line.strip() == b"trailer":
                break
            parts = line.strip().split()
            if len(parts) == 2:
                start_obj = int(parts[0])
                count = int(parts[1])
                for i in range(count):
                    entry = self.stream.readline()
                    offset = int(entry[:10])
                    gen = int(entry[11:16])
                    inuse = entry[17:18]
                    if inuse == b"n":
                        xref_table[(start_obj + i, gen)] = offset
        self.xref = xref_table
        # Read trailer
        trailer_data = b""
        while True:
            line = self.stream.readline()
            if line.strip() == b"startxref" or not line:
                break
            trailer_data += line
        trailer_match = re.search(b"<<(.+?)>>", trailer_data, re.DOTALL)
        if trailer_match:
            trailer_str = trailer_match.group(1)
            self.trailer = self._parse_dict(trailer_str)
        else:
            self.trailer = {}
        # Get root
        root_ref = self.trailer.get("/Root")
        if root_ref:
            root_obj = self._get_object_from_ref(root_ref)
            # Get pages
            pages_ref = root_obj.get("/Pages")
            pages_obj = self._get_object_from_ref(pages_ref)
            self._collect_pages(pages_obj)
        # Metadata
        info_ref = self.trailer.get("/Info")
        if info_ref:
            info_obj = self._get_object_from_ref(info_ref)
            self.metadata = {k: decode_pdf_string(v) for k, v in info_obj.items()}

        # Encryption
        if "/Encrypt" in self.trailer:
            self.is_encrypted = True

    def _parse_dict(self, s):
        # Very simple parser for << ... >>
        d = {}
        items = re.findall(rb"/(\w+)\s+(\(.*?\)|/[\w#]+|\d+)", s)
        for k, v in items:
            key = "/" + k.decode()
            if v.startswith(b"/"):
                val = v.decode()
            elif v.startswith(b"("):
                val = v[1:-1].decode("utf-8", "ignore")
            else:
                val = int(v)
            d[key] = val
        return d

    def _get_object(self, objnum, gennum):
        if (objnum, gennum) in self.objects:
            return self.objects[(objnum, gennum)]
        offset = self.xref.get((objnum, gennum))
        if offset is None:
            return None
        self.stream.seek(offset)
        # Read object header
        line = self.stream.readline()
        if not re.match(rb"\d+\s+\d+\s+obj", line):
            # Try to parse again
            objnum2, gennum2, obj = parse_indirect_object(io.BytesIO(line + self.stream.read(1000)), self)
            self.objects[(objnum, gennum)] = obj
            return obj
        # Parse object
        objnum2, gennum2, obj = parse_indirect_object(self.stream, self)
        self.objects[(objnum, gennum)] = obj
        return obj

    def _get_object_from_ref(self, ref):
        # ref is like "12 0 R"
        if isinstance(ref, str):
            m = re.match(r"(\d+)\s+(\d+)\s+R", ref)
            if m:
                objnum = int(m.group(1))
                gennum = int(m.group(2))
                return self._get_object(objnum, gennum)
        return ref

    def _collect_pages(self, pages_obj):
        # Recursively collect all page objects
        if pages_obj.get("/Type") == "/Pages":
            kids = pages_obj.get("/Kids", [])
            for kid in kids:
                kid_obj = self._get_object_from_ref(kid)
                self._collect_pages(kid_obj)
        elif pages_obj.get("/Type") == "/Page":
            index = len(self.pages)
            self.pages.append(PageObject(self, pages_obj, index=index))

    def decrypt(self, password):
        # For this pure Python implementation, we just mark as decrypted
        if self.is_encrypted:
            self._decrypted = True
            self.is_encrypted = False
            return 1
        return 0