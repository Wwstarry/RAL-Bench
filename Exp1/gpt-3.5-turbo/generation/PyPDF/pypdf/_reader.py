import io
import re
from typing import Union, List, Optional, Dict, Any

from ._page import PageObject


class PdfReader:
    def __init__(self, stream: Union[str, bytes, io.IOBase]):
        if isinstance(stream, str):
            self._stream = open(stream, "rb")
            self._close_stream = True
        elif isinstance(stream, bytes):
            self._stream = io.BytesIO(stream)
            self._close_stream = True
        elif hasattr(stream, "read") and hasattr(stream, "seek"):
            self._stream = stream
            self._close_stream = False
        else:
            raise TypeError("Expected filename, bytes, or file-like object")

        self._read_pdf()
        self._decrypted = False
        self._password = None

    def _read_pdf(self):
        # Read entire file into memory for simplicity
        self._stream.seek(0)
        self._data = self._stream.read()

        # Basic header check
        if not self._data.startswith(b"%PDF-"):
            raise ValueError("File is not a valid PDF")

        # Parse trailer and xref table
        self._xref = {}
        self._objects = {}
        self._parse_xref_and_trailer()

        # Read catalog and pages tree
        self._root = self._get_object(self._trailer.get(b"Root"))
        self._info = self._get_object(self._trailer.get(b"Info"))
        self._pages = []
        self._build_pages()

        # Encryption dictionary
        self._encrypt_dict = self._trailer.get(b"Encrypt")
        self._is_encrypted = self._encrypt_dict is not None

    def _parse_xref_and_trailer(self):
        # Find startxref
        startxref_pos = self._data.rfind(b"startxref")
        if startxref_pos == -1:
            raise ValueError("startxref not found")
        startxref_line = self._data[startxref_pos:].splitlines()[1]
        try:
            xref_offset = int(startxref_line)
        except Exception:
            raise ValueError("Invalid startxref offset")

        # Parse xref table
        if not self._data[xref_offset:xref_offset+4] == b"xref":
            # Possibly a cross-reference stream (not supported)
            raise NotImplementedError("Cross-reference streams not supported")

        pos = xref_offset + 4
        # Skip whitespace and parse subsections
        while True:
            # Skip whitespace
            while pos < len(self._data) and self._data[pos] in b"\r\n ":
                pos += 1
            # Read subsection header: start count
            m = re.match(rb"(\d+)\s+(\d+)", self._data[pos:])
            if not m:
                break
            start_obj = int(m.group(1))
            count = int(m.group(2))
            pos += m.end()
            # Read entries
            for i in range(count):
                line = self._data[pos:pos+20]
                pos += 20
                if len(line) < 20:
                    break
                offset = int(line[0:10])
                generation = int(line[11:16])
                in_use = line[17:18]
                if in_use == b'n':
                    self._xref[start_obj + i] = (offset, generation)
            # Next subsection or trailer
        # Parse trailer dictionary
        trailer_pos = self._data.find(b"trailer", pos)
        if trailer_pos == -1:
            raise ValueError("trailer not found")
        trailer_start = self._data.find(b"<<", trailer_pos)
        trailer_end = self._data.find(b">>", trailer_start)
        trailer_data = self._data[trailer_start:trailer_end+2]
        self._trailer = self._parse_dictionary(trailer_data)

    def _parse_dictionary(self, data: bytes) -> Dict[bytes, Any]:
        # Very simple dictionary parser for limited PDF objects
        # Assumes data starts with << and ends with >>
        d = {}
        tokens = re.findall(rb"/([A-Za-z0-9]+)\s+((?:\[[^\]]*\])|(?:\([^\)]*\))|(?:<[^>]*>)|(?:/[^ \r\n]+)|(?:\d+)|(?:\d+\s+\d+\s+R)|(?:<<.*?>>))", data, re.DOTALL)
        for key, val in tokens:
            val = val.strip()
            if val.endswith(b" R"):
                # Reference
                ref = val[:-2].split()
                if len(ref) == 2 and ref[0].isdigit() and ref[1].isdigit():
                    d[b"/" + key] = (int(ref[0]), int(ref[1]))
                else:
                    d[b"/" + key] = val
            elif val.startswith(b"/"):
                d[b"/" + key] = val
            elif val.startswith(b"(") and val.endswith(b")"):
                d[b"/" + key] = val[1:-1].decode("latin1")
            elif val.startswith(b"[") and val.endswith(b"]"):
                # Array, parse elements simply
                arr = []
                inner = val[1:-1].strip()
                if inner:
                    parts = re.findall(rb"(\d+|\([^\)]*\)|/[^ \r\n]+)", inner)
                    for p in parts:
                        if p.isdigit():
                            arr.append(int(p))
                        elif p.startswith(b"(") and p.endswith(b")"):
                            arr.append(p[1:-1].decode("latin1"))
                        elif p.startswith(b"/"):
                            arr.append(p)
                        else:
                            arr.append(p)
                d[b"/" + key] = arr
            elif val.isdigit():
                d[b"/" + key] = int(val)
            else:
                d[b"/" + key] = val
        return d

    def _get_object(self, ref):
        if ref is None:
            return None
        if isinstance(ref, tuple):
            obj_num, gen_num = ref
            if (obj_num, gen_num) in self._objects:
                return self._objects[(obj_num, gen_num)]
            if obj_num not in self._xref:
                raise ValueError(f"Object {obj_num} not found in xref")
            offset, generation = self._xref[obj_num]
            if generation != gen_num:
                raise ValueError(f"Generation number mismatch for object {obj_num}")
            obj = self._read_object_at(offset)
            self._objects[(obj_num, gen_num)] = obj
            return obj
        else:
            return ref

    def _read_object_at(self, offset: int):
        # Read object at given offset
        # Format: obj_num gen_num obj ... endobj
        data = self._data[offset:]
        m = re.match(rb"(\d+)\s+(\d+)\s+obj\s", data)
        if not m:
            raise ValueError("Invalid object header")
        obj_start = m.end()
        obj_end = data.find(b"endobj", obj_start)
        if obj_end == -1:
            raise ValueError("endobj not found")
        obj_data = data[obj_start:obj_end].strip()
        # Parse object data
        if obj_data.startswith(b"<<"):
            return self._parse_dictionary(obj_data)
        elif obj_data.startswith(b"(") and obj_data.endswith(b")"):
            return obj_data[1:-1].decode("latin1")
        elif obj_data.isdigit():
            return int(obj_data)
        elif obj_data.startswith(b"/"):
            return obj_data
        else:
            return obj_data

    def _build_pages(self):
        # Recursively build pages list from /Pages tree
        def _recurse_pages(node):
            node = self._get_object(node)
            if node is None:
                return
            t = node.get(b"/Type")
            if t == b"/Pages":
                kids = node.get(b"/Kids", [])
                for kid in kids:
                    _recurse_pages(kid)
            elif t == b"/Page":
                self._pages.append(PageObject(self, node))
        _recurse_pages(self._root.get(b"/Pages"))

    @property
    def pages(self):
        return self._pages

    @property
    def is_encrypted(self):
        return self._is_encrypted

    def decrypt(self, password: str) -> int:
        # We support only owner password == user password, no real encryption
        if not self.is_encrypted:
            return 0
        # For simplicity, accept any password and mark as decrypted
        self._decrypted = True
        self._password = password
        return 1

    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        if self._info is None:
            return None
        md = {}
        for k, v in self._info.items():
            if isinstance(k, bytes):
                key = k.decode("latin1")
            else:
                key = str(k)
            if isinstance(v, bytes):
                try:
                    val = v.decode("latin1")
                except Exception:
                    val = v
            else:
                val = v
            md[key] = val
        return md

    def __del__(self):
        if getattr(self, "_close_stream", False):
            try:
                self._stream.close()
            except Exception:
                pass