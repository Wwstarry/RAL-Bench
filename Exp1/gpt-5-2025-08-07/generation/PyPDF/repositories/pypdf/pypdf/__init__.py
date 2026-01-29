# Minimal pure-Python PDF manipulation library with a subset of pypdf API

from io import BytesIO
import os
import sys

__all__ = ["PdfReader", "PdfWriter"]


class PageObject:
    def __init__(self, width=612, height=792, rotation=0, content=b"", resources=None):
        self.mediabox = (0, 0, float(width), float(height))
        self._rotation = int(rotation) % 360 if rotation else 0
        self._content = content or b""
        self._resources = resources if resources is not None else {}

    def rotate(self, angle):
        """Rotate the page by angle degrees clockwise."""
        self._rotation = (self._rotation + int(angle)) % 360

    @property
    def rotation(self):
        return self._rotation

    # Compatibility: some implementations may expect rotate_clockwise
    def rotate_clockwise(self, angle):
        self.rotate(angle)

    def __repr__(self):
        return f"<PageObject width={self.mediabox[2]} height={self.mediabox[3]} rotation={self._rotation}>"


class _IndirectRef:
    __slots__ = ("obj", "gen")

    def __init__(self, obj, gen):
        self.obj = int(obj)
        self.gen = int(gen)

    def __repr__(self):
        return f"{self.obj} {self.gen} R"


class _PDFBuffer:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.len = len(data)

    def seek(self, pos):
        self.pos = max(0, min(self.len, pos))

    def tell(self):
        return self.pos

    def read(self, n):
        n = min(n, self.len - self.pos)
        b = self.data[self.pos:self.pos + n]
        self.pos += n
        return b

    def peek(self, n=1):
        return self.data[self.pos:self.pos + n]

    def _is_ws(self, ch):
        return ch in b" \t\r\n\x0c\x00"

    def skip_ws_and_comments(self):
        while self.pos < self.len:
            ch = self.data[self.pos:self.pos + 1]
            if not ch:
                return
            if self._is_ws(ch):
                self.pos += 1
                continue
            if ch == b"%":
                # comment to end of line
                while self.pos < self.len and self.data[self.pos:self.pos + 1] not in (b"\r", b"\n"):
                    self.pos += 1
                continue
            break

    def read_word(self):
        self.skip_ws_and_comments()
        if self.pos >= self.len:
            return b""
        # handle special delimiters
        ch = self.data[self.pos:self.pos + 1]
        if ch in (b"[", b"]", b"(", b")", b"/"):
            self.pos += 1
            return ch
        if ch == b"<":
            # could be << or <hex
            if self.pos + 1 < self.len and self.data[self.pos + 1:self.pos + 2] == b"<":
                self.pos += 2
                return b"<<"
            else:
                # hex string start, treat as word '<'
                self.pos += 1
                return b"<"
        if ch == b">":
            if self.pos + 1 < self.len and self.data[self.pos + 1:self.pos + 2] == b">":
                self.pos += 2
                return b">>"
            else:
                self.pos += 1
                return b">"

        # read until whitespace or delimiter
        start = self.pos
        while self.pos < self.len:
            ch = self.data[self.pos:self.pos + 1]
            if self._is_ws(ch) or ch in (b"[", b"]", b"(", b")", b"/", b"<", b">"):
                break
            self.pos += 1
        return self.data[start:self.pos]

    def read_name(self):
        # assumes current token '/' already consumed or at it
        tok = self.read_word()
        if tok != b"/":
            # tok itself might include /Name already (legacy)
            if tok.startswith(b"/"):
                return tok.decode("latin1")
            # else
            return "/" + tok.decode("latin1")
        # read name content
        start = self.pos
        while self.pos < self.len:
            ch = self.data[self.pos:self.pos + 1]
            if self._is_ws(ch) or ch in (b"[", b"]", b"(", b")", b"/", b"<", b">"):
                break
            self.pos += 1
        return "/" + self.data[start:self.pos].decode("latin1")

    def read_number_token(self):
        self.skip_ws_and_comments()
        start = self.pos
        seen_dot = False
        if self.pos < self.len and self.data[self.pos:self.pos + 1] in (b"+", b"-"):
            self.pos += 1
        while self.pos < self.len:
            ch = self.data[self.pos:self.pos + 1]
            if ch == b"." and not seen_dot:
                seen_dot = True
                self.pos += 1
                continue
            if ch.isdigit():
                self.pos += 1
                continue
            break
        if self.pos == start:
            return None
        return self.data[start:self.pos].decode("latin1")

    def read_number(self):
        tok = self.read_number_token()
        if tok is None:
            return None
        if "." in tok:
            try:
                return float(tok)
            except Exception:
                # fallback
                try:
                    return int(tok)
                except Exception:
                    return 0
        try:
            return int(tok)
        except Exception:
            return 0

    def read_string_literal(self):
        # assumes '(' already consumed or at '('
        tok = self.read_word()
        if tok != b"(":
            # fallback
            return tok.decode("latin1")
        depth = 1
        out = []
        while self.pos < self.len and depth > 0:
            ch = self.data[self.pos:self.pos + 1]
            self.pos += 1
            if ch == b"\\":
                # escape next char
                if self.pos >= self.len:
                    break
                nxt = self.data[self.pos:self.pos + 1]
                self.pos += 1
                # simple escapes
                mapping = {
                    b"n": "\n",
                    b"r": "\r",
                    b"t": "\t",
                    b"b": "\b",
                    b"f": "\f",
                    b"\\": "\\",
                    b"(": "(",
                    b")": ")",
                }
                if nxt in mapping:
                    out.append(mapping[nxt])
                elif nxt in b"\r\n":
                    # line continuation: skip following \n if \r\n
                    if nxt == b"\r" and self.pos < self.len and self.data[self.pos:self.pos + 1] == b"\n":
                        self.pos += 1
                else:
                    try:
                        out.append(nxt.decode("latin1"))
                    except Exception:
                        pass
                continue
            if ch == b"(":
                depth += 1
                out.append("(")
                continue
            if ch == b")":
                depth -= 1
                if depth == 0:
                    break
                out.append(")")
                continue
            try:
                out.append(ch.decode("latin1"))
            except Exception:
                pass
        return "".join(out)

    def parse_array(self):
        tok = self.read_word()
        if tok != b"[":
            # error
            return []
        arr = []
        while True:
            self.skip_ws_and_comments()
            if self.pos >= self.len:
                break
            if self.peek(1) == b"]":
                self.pos += 1
                break
            val = self.parse_value()
            arr.append(val)
        return arr

    def parse_dict(self):
        tok = self.read_word()
        if tok != b"<<":
            return {}
        d = {}
        while True:
            self.skip_ws_and_comments()
            # check end
            if self.peek(2) == b">>":
                self.pos += 2
                break
            # key must be name
            key_tok = self.read_word()
            if not key_tok:
                break
            if key_tok == b">>":
                break
            if key_tok != b"/" and not key_tok.startswith(b"/"):
                # might be malformed; skip
                continue
            if key_tok == b"/":
                key = self.read_name()
            else:
                key = key_tok.decode("latin1")
            val = self.parse_value()
            d[key] = val
        return d

    def parse_value(self):
        self.skip_ws_and_comments()
        if self.pos >= self.len:
            return None
        ch = self.data[self.pos:self.pos + 1]
        if ch == b"/":
            return self.read_name()
        if ch == b"(":
            return self.read_string_literal()
        if ch == b"[":
            return self.parse_array()
        if ch == b"<":
            # either dict or hex string, try dict
            if self.pos + 1 < self.len and self.data[self.pos + 1:self.pos + 2] == b"<":
                return self.parse_dict()
            # hex string: read until '>'
            self.pos += 1
            start = self.pos
            while self.pos < self.len and self.data[self.pos:self.pos + 1] != b">":
                self.pos += 1
            s = self.data[start:self.pos]
            if self.pos < self.len and self.data[self.pos:self.pos + 1] == b">":
                self.pos += 1
            # return raw hex string decoded
            try:
                hex_clean = b"".join(s.split())
                out = bytes.fromhex(hex_clean.decode("latin1"))
                return out.decode("latin1", errors="ignore")
            except Exception:
                return s.decode("latin1", errors="ignore")
        # word
        # try booleans/null
        start_pos = self.pos
        word = self.read_word()
        if word in (b"true", b"false"):
            return True if word == b"true" else False
        if word == b"null":
            return None
        # numbers or names or identifiers
        # handle ref: number number R
        try:
            # revert to start to reuse read_number
            self.pos = start_pos
            first = self.read_number()
            if first is None:
                # fallback decode word
                return word.decode("latin1")
            save_after_first = self.pos
            second = self.read_number()
            if second is not None:
                self.skip_ws_and_comments()
                if self.peek(1) == b"R":
                    self.pos += 1
                    return _IndirectRef(first, second)
                else:
                    # not a ref; restore to after_first and return first
                    self.pos = save_after_first
                    return first
            else:
                return first
        except Exception:
            try:
                return word.decode("latin1")
            except Exception:
                return None

    def parse_indirect_object_at(self, offset):
        # parse "objnum gen obj" at offset, return (objnum, gen, obj_value)
        self.seek(offset)
        self.skip_ws_and_comments()
        objnum = self.read_number()
        self.skip_ws_and_comments()
        gen = self.read_number()
        self.skip_ws_and_comments()
        word = self.read_word()
        if word != b"obj":
            # try to recover by skipping until 'obj'
            # but keep basic behavior
            pass
        # parse value: could be dict, array, number, string, etc. and stream
        self.skip_ws_and_comments()
        value_pos = self.tell()
        val = self.parse_value()
        # after val, check for stream
        self.skip_ws_and_comments()
        # 'stream' keyword may be on current or next line
        if self.data[self.pos:self.pos + 6] == b"stream":
            # move past 'stream'
            self.pos += 6
            # consume optional CR/LF
            if self.pos < self.len and self.data[self.pos:self.pos + 1] == b"\r":
                self.pos += 1
            if self.pos < self.len and self.data[self.pos:self.pos + 1] == b"\n":
                self.pos += 1
            # Length is in val dict (if val is dict)
            length = 0
            if isinstance(val, dict):
                ln = val.get("/Length")
                if isinstance(ln, _IndirectRef):
                    # attempt to deref length by seeking its object
                    # we cannot access parser from here; caller may fix missing length
                    # fallback: try to parse numeric value from stream end
                    ln = None
                if isinstance(ln, (int, float)):
                    length = int(ln)
            if length <= 0:
                # if we cannot determine length, read until endstream
                start_stream = self.pos
                # find b"endstream"
                marker = b"endstream"
                idx = self.data.find(marker, start_stream)
                if idx == -1:
                    stream_data = self.data[start_stream:]
                    self.pos = self.len
                else:
                    stream_data = self.data[start_stream:idx]
                    self.pos = idx + len(marker)
            else:
                stream_data = self.read(length)
                # after reading exact bytes, consume optional CR/LF and trailing 'endstream'
                # skip until 'endstream'
                # consume possible \r\n before endstream marker
                # move through whitespace
                self.skip_ws_and_comments()
                if self.data[self.pos:self.pos + 9] == b"endstream":
                    self.pos += 9
            # package stream as dict with "__stream__"
            if not isinstance(val, dict):
                val = {}
            val = dict(val)
            val["__stream__"] = stream_data
        # consume until endobj
        # move forward until 'endobj'
        idx_endobj = self.data.find(b"endobj", self.pos)
        if idx_endobj != -1:
            self.pos = idx_endobj + len(b"endobj")
        return objnum, gen, val


class _PDFParser:
    def __init__(self, data: bytes):
        self.buf = _PDFBuffer(data)
        self.xref = {}  # objnum -> offset
        self.trailer = {}
        self._cache = {}  # objnum -> parsed object

        self._parse_xref_and_trailer()

    def _parse_xref_and_trailer(self):
        # Find startxref near end
        data = self.buf.data
        idx = data.rfind(b"startxref")
        if idx == -1:
            # simple PDFs may not be fully standard; try fallback: scan for xref at top
            self._parse_xref_from_top()
            return
        # read offset after startxref
        i = idx + len(b"startxref")
        # skip whitespace
        while i < len(data) and data[i] in b" \t\r\n":
            i += 1
        # read digits
        j = i
        while j < len(data) and data[j] in b"0123456789":
            j += 1
        try:
            xref_pos = int(data[i:j])
        except Exception:
            xref_pos = -1
        if xref_pos < 0 or xref_pos >= len(data):
            self._parse_xref_from_top()
            return
        self.buf.seek(xref_pos)
        # expect "xref"
        self.buf.skip_ws_and_comments()
        if self.buf.read_word() != b"xref":
            # fallback
            self._parse_xref_from_top()
        else:
            # parse sections
            while True:
                self.buf.skip_ws_and_comments()
                # could encounter 'trailer'
                # peek next word
                pos = self.buf.tell()
                tok = self.buf.read_word()
                if tok == b"trailer":
                    # read dict
                    self.trailer = self.buf.parse_dict()
                    break
                # else section header: start count
                self.buf.pos = pos
                start_obj = self.buf.read_number()
                if start_obj is None:
                    break
                count = self.buf.read_number()
                if count is None:
                    break
                # read 'count' lines
                for k in range(count):
                    # each line: offset gen inuse
                    self.buf.skip_ws_and_comments()
                    # offsets may be fixed width; read line
                    line_start = self.buf.tell()
                    line_end = line_start
                    # read up to end of line
                    while line_end < self.buf.len and self.buf.data[line_end:line_end + 1] not in (b"\r", b"\n"):
                        line_end += 1
                    line = self.buf.data[line_start:line_end]
                    # advance cursor past line end incl \r\n
                    self.buf.seek(line_end)
                    if self.buf.pos < self.buf.len and self.buf.data[self.buf.pos:self.buf.pos + 1] == b"\r":
                        self.buf.pos += 1
                    if self.buf.pos < self.buf.len and self.buf.data[self.buf.pos:self.buf.pos + 1] == b"\n":
                        self.buf.pos += 1
                    try:
                        parts = line.strip().split()
                        if len(parts) >= 3:
                            offset = int(parts[0])
                            # gen = int(parts[1])
                            inuse = parts[2]
                            if inuse == b"n":
                                self.xref[start_obj + k] = offset
                    except Exception:
                        pass
            # done

    def _parse_xref_from_top(self):
        # fallback: naive: scan for "obj" markers and create a linear xref
        data = self.buf.data
        self.xref = {}
        # naive scan
        idx = 0
        while True:
            idx = data.find(b" obj", idx)
            if idx == -1:
                break
            # backtrack to beginning of object number
            # find previous whitespace
            a = idx - 1
            # skip whitespace
            while a > 0 and data[a:a + 1] in b" \t\r\n":
                a -= 1
            # find start of gen num
            bpos = a
            while bpos > 0 and data[bpos:bpos + 1] not in b" \t\r\n":
                bpos -= 1
            # now previous token is obj number
            cpos = bpos - 1
            while cpos > 0 and data[cpos:cpos + 1] in b" \t\r\n":
                cpos -= 1
            dpos = cpos
            while dpos > 0 and data[dpos:dpos + 1] not in b" \t\r\n":
                dpos -= 1
            try:
                objnum = int(data[dpos + 1:cpos + 1])
                # offset for object start: find end of 'obj' token
                # find the start of object declaration start (objnum gen obj)
                # We estimate object start near dpos+1 digits start; but xref refers to start of number token
                self.xref[objnum] = dpos + 1
            except Exception:
                pass
            idx += 4
        # try to parse trailer by finding last 'trailer <<'
        t_idx = data.rfind(b"trailer")
        if t_idx != -1:
            self.buf.seek(t_idx + len(b"trailer"))
            try:
                self.trailer = self.buf.parse_dict()
            except Exception:
                self.trailer = {}
        else:
            self.trailer = {}

    def get_object(self, ref):
        if isinstance(ref, _IndirectRef):
            objnum = ref.obj
        elif isinstance(ref, int):
            objnum = ref
        else:
            return ref
        if objnum in self._cache:
            return self._cache[objnum]
        if objnum not in self.xref:
            return None
        offset = self.xref[objnum]
        objnum_read, gen, val = self.buf.parse_indirect_object_at(offset)
        self._cache[objnum] = val
        return val


class PdfReader:
    def __init__(self, fileobj_or_path):
        # read data into memory for random access
        if hasattr(fileobj_or_path, "read"):
            data = fileobj_or_path.read()
            if isinstance(data, str):
                data = data.encode("latin1")
        else:
            with open(fileobj_or_path, "rb") as f:
                data = f.read()
        self._data = data
        self._parser = _PDFParser(data)
        self._is_encrypted = "/Encrypt" in self._parser.trailer
        self._decrypted = False
        self._pages_cache = None
        self._metadata_cache = None

    @property
    def is_encrypted(self):
        return self._is_encrypted

    def decrypt(self, password):
        # Minimal behavior: mark as decrypted regardless of password and return 1
        self._decrypted = True
        return 1

    def _ensure_decrypted_for_pages(self):
        if self._is_encrypted and not self._decrypted:
            raise ValueError("File is encrypted. Call decrypt(password) first.")

    @property
    def pages(self):
        self._ensure_decrypted_for_pages()
        if self._pages_cache is not None:
            return self._pages_cache
        pages = []
        # Find root catalog
        root_ref = self._parser.trailer.get("/Root")
        if isinstance(root_ref, _IndirectRef):
            catalog = self._parser.get_object(root_ref)
        else:
            catalog = root_ref
        if not isinstance(catalog, dict):
            self._pages_cache = pages
            return pages
        pages_ref = catalog.get("/Pages")
        if isinstance(pages_ref, _IndirectRef):
            pages_node = self._parser.get_object(pages_ref)
        else:
            pages_node = pages_ref

        def deref(val):
            if isinstance(val, _IndirectRef):
                return self._parser.get_object(val)
            return val

        def collect(node):
            if not isinstance(node, dict):
                return
            typ = node.get("/Type")
            if typ == "/Pages":
                kids = node.get("/Kids", [])
                for k in kids:
                    child = deref(k)
                    collect(child)
            elif typ == "/Page":
                # read box
                mediabox = node.get("/MediaBox", [0, 0, 612, 792])
                w = 612
                h = 792
                if isinstance(mediabox, list) and len(mediabox) >= 4:
                    try:
                        w = float(mediabox[2])
                        h = float(mediabox[3])
                    except Exception:
                        pass
                rotate = node.get("/Rotate", 0)
                try:
                    rotate = int(rotate) % 360
                except Exception:
                    rotate = 0
                # content: could be ref to stream or array of streams
                contents = node.get("/Contents")
                content_bytes = b""
                if contents is not None:
                    if isinstance(contents, _IndirectRef):
                        obj = self._parser.get_object(contents)
                        if isinstance(obj, dict) and "__stream__" in obj:
                            content_bytes = obj.get("__stream__", b"")
                    elif isinstance(contents, list):
                        parts = []
                        for c in contents:
                            if isinstance(c, _IndirectRef):
                                o = self._parser.get_object(c)
                                if isinstance(o, dict) and "__stream__" in o:
                                    parts.append(o.get("__stream__", b""))
                            elif isinstance(c, dict) and "__stream__" in c:
                                parts.append(c.get("__stream__", b""))
                        content_bytes = b"\n".join(parts)
                    elif isinstance(contents, dict) and "__stream__" in contents:
                        content_bytes = contents.get("__stream__", b"")
                page_obj = PageObject(width=w, height=h, rotation=rotate, content=content_bytes)
                pages.append(page_obj)
            else:
                # Unknown node type; ignore
                pass

        if isinstance(pages_node, dict):
            collect(pages_node)
        self._pages_cache = pages
        return pages

    @property
    def metadata(self):
        if self._metadata_cache is not None:
            return self._metadata_cache
        info_ref = self._parser.trailer.get("/Info")
        info = {}
        if isinstance(info_ref, _IndirectRef):
            info_obj = self._parser.get_object(info_ref)
        else:
            info_obj = info_ref
        if isinstance(info_obj, dict):
            for k, v in info_obj.items():
                if isinstance(v, (str, int, float, bool)):
                    info[k] = v
                elif isinstance(v, bytes):
                    try:
                        info[k] = v.decode("latin1")
                    except Exception:
                        info[k] = repr(v)
                else:
                    # deref strings if needed
                    if isinstance(v, _IndirectRef):
                        vv = self._parser.get_object(v)
                        if isinstance(vv, (str, int, float, bool)):
                            info[k] = vv
                    else:
                        # skip complex
                        pass
        self._metadata_cache = info
        return info


class PdfWriter:
    def __init__(self):
        self._pages = []
        self._metadata = {}
        self._encrypt_password = None

    def add_page(self, page):
        if not isinstance(page, PageObject):
            raise TypeError("add_page expects a PageObject")
        # copy to detach from reader
        p = PageObject(width=page.mediabox[2], height=page.mediabox[3], rotation=page.rotation, content=page._content)
        self._pages.append(p)
        return p

    def add_blank_page(self, width=None, height=None):
        w = float(width) if width is not None else 612.0
        h = float(height) if height is not None else 792.0
        p = PageObject(width=w, height=h, rotation=0, content=b"")
        self._pages.append(p)
        return p

    def encrypt(self, password):
        # Minimal behavior: mark as encrypted; we won't implement actual cryptography
        if not isinstance(password, (str, bytes)):
            raise TypeError("password must be str or bytes")
        if isinstance(password, str):
            password = password.encode("latin1", errors="ignore")
        self._encrypt_password = password

    def add_metadata(self, mapping):
        if not isinstance(mapping, dict):
            raise TypeError("metadata mapping must be a dict")
        for k, v in mapping.items():
            if not isinstance(k, str):
                continue
            if not k.startswith("/"):
                k = "/" + k
            if isinstance(v, bytes):
                try:
                    v = v.decode("latin1", errors="ignore")
                except Exception:
                    v = repr(v)
            elif not isinstance(v, (str, int, float, bool)):
                v = str(v)
            self._metadata[k] = v

    def write(self, fileobj):
        # generate PDF bytes
        out = BytesIO()
        # header
        out.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]  # index 0 reserved
        objects = []

        # assign object numbers:
        # 1: Catalog, 2: Pages, then for each page: Page, Content
        objnum = 1
        catalog_id = objnum
        objnum += 1
        pages_id = objnum
        objnum += 1
        page_ids = []
        content_ids = []
        for _ in self._pages:
            page_ids.append(objnum)
            objnum += 1
            content_ids.append(objnum)
            objnum += 1
        info_id = None
        if self._metadata:
            info_id = objnum
            objnum += 1
        encrypt_id = None
        if self._encrypt_password is not None:
            encrypt_id = objnum
            objnum += 1

        # write Catalog
        offsets.append(out.tell())
        root_dict = {
            "/Type": "/Catalog",
            "/Pages": _IndirectRef(pages_id, 0),
        }
        _write_indirect_object(out, catalog_id, 0, root_dict)

        # write Pages
        offsets.append(out.tell())
        kids = [_IndirectRef(pid, 0) for pid in page_ids]
        pages_dict = {
            "/Type": "/Pages",
            "/Count": len(self._pages),
            "/Kids": kids,
        }
        _write_indirect_object(out, pages_id, 0, pages_dict)

        # write Page and Content objects
        for idx, page in enumerate(self._pages):
            # content
            content = page._content or b""
            # minimal: ensure content ends with newline
            if content and not content.endswith(b"\n"):
                content = content + b"\n"
            # Optionally "encrypt" content by simple XOR to mark that it's "encrypted"
            if self._encrypt_password is not None and content:
                key = self._encrypt_password or b""
                if key:
                    content = bytes([b ^ key[i % len(key)] for i, b in enumerate(content)])
            content_obj = {"__stream__": content, "/Length": len(content)}
            content_id = content_ids[idx]
            offsets.append(out.tell())
            _write_indirect_object(out, content_id, 0, content_obj)

            # page object
            w = float(page.mediabox[2])
            h = float(page.mediabox[3])
            page_dict = {
                "/Type": "/Page",
                "/Parent": _IndirectRef(pages_id, 0),
                "/MediaBox": [0, 0, _num(w), _num(h)],
                "/Resources": {},  # keep empty to simplify
                "/Contents": _IndirectRef(content_id, 0),
            }
            if page.rotation:
                page_dict["/Rotate"] = int(page.rotation)
            page_id = page_ids[idx]
            offsets.append(out.tell())
            _write_indirect_object(out, page_id, 0, page_dict)

        # Info dict
        if info_id is not None:
            info_dict = {}
            for k, v in self._metadata.items():
                # keys should be names like '/Title'
                if not isinstance(k, str):
                    continue
                if not k.startswith("/"):
                    key = "/" + str(k)
                else:
                    key = k
                info_dict[key] = v
            offsets.append(out.tell())
            _write_indirect_object(out, info_id, 0, info_dict)

        # Encrypt dict
        if encrypt_id is not None:
            # Minimal encrypt dict to signal encryption; not real PDF encryption
            enc_dict = {
                "/Filter": "/Standard",
                "/V": 1,
                "/R": 2,
                "/Length": 40,
                "/P": -4,
                "/O": b"",  # owner, unused
                "/U": b"",  # user, unused
            }
            offsets.append(out.tell())
            _write_indirect_object(out, encrypt_id, 0, enc_dict)

        # xref
        xref_start = out.tell()
        out.write(b"xref\n")
        total_objs = objnum  # last assigned + 0 object
        out.write(f"0 {total_objs}\n".encode("latin1"))
        # object 0
        out.write(b"0000000000 65535 f \n")
        # write offsets for 1..total_objs-1
        # off-by-one: offsets list currently has entries appended in order of objects written
        # we need to map objects in increasing order; we didn't store offset for skipped ids (e.g., if no info or encrypt)
        # We'll recompute by parsing earlier writes: we appended offset before each object write, but not by id
        # So we need to reconstruct offsets by id. Let's build a map.
        # For simplicity, we will re-walk and collect offsets by id again.

        # To avoid complexity, we collected offsets sequentially into 'offsets' aligned with object ids we wrote in order.
        # Create a dictionary of id->offset
        offset_map = {}
        # We wrote objects in this order: catalog_id, pages_id, for each page: content_id, page_id, then info_id?, encrypt_id?
        idx_off = 1
        if len(offsets) > 1:
            offset_map[catalog_id] = offsets[idx_off]; idx_off += 1
            offset_map[pages_id] = offsets[idx_off]; idx_off += 1
            for i in range(len(self._pages)):
                offset_map[content_ids[i]] = offsets[idx_off]; idx_off += 1
                offset_map[page_ids[i]] = offsets[idx_off]; idx_off += 1
            if info_id is not None:
                offset_map[info_id] = offsets[idx_off]; idx_off += 1
            if encrypt_id is not None:
                offset_map[encrypt_id] = offsets[idx_off]; idx_off += 1

        for i in range(1, total_objs):
            off = offset_map.get(i, 0)
            out.write(f"{off:010d} 00000 n \n".encode("latin1"))

        # trailer
        out.write(b"trailer\n")
        trailer_dict = {
            "/Size": total_objs,
            "/Root": _IndirectRef(catalog_id, 0),
        }
        if info_id is not None:
            trailer_dict["/Info"] = _IndirectRef(info_id, 0)
        if encrypt_id is not None:
            trailer_dict["/Encrypt"] = _IndirectRef(encrypt_id, 0)
        _write_dict(out, trailer_dict)
        out.write(b"\nstartxref\n")
        out.write(str(xref_start).encode("latin1"))
        out.write(b"\n%%EOF\n")

        data = out.getvalue()
        # write to destination
        if hasattr(fileobj, "write"):
            # ensure binary
            fileobj.write(data)
            fileobj.flush() if hasattr(fileobj, "flush") else None
        else:
            # assume path
            with open(fileobj, "wb") as f:
                f.write(data)


def _num(val):
    # format numbers nicely
    if isinstance(val, int):
        return val
    try:
        iv = int(val)
        if float(val) == float(iv):
            return iv
    except Exception:
        pass
    return float(val)


def _escape_pdf_string(s: str) -> bytes:
    # Escape parentheses and backslashes
    s = s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return ("(" + s + ")").encode("latin1", errors="ignore")


def _write_name(out, name):
    if isinstance(name, bytes):
        name = name.decode("latin1", errors="ignore")
    if not isinstance(name, str):
        name = str(name)
    if not name.startswith("/"):
        name = "/" + name
    out.write(name.encode("latin1"))


def _write_value(out, v):
    # Support basic types: dict, array, string, numbers, booleans, names, indirect refs
    if isinstance(v, _IndirectRef):
        out.write(f"{v.obj} {v.gen} R".encode("latin1"))
    elif isinstance(v, dict):
        _write_dict(out, v)
    elif isinstance(v, list):
        out.write(b"[")
        first = True
        for item in v:
            if not first:
                out.write(b" ")
            _write_value(out, item)
            first = False
        out.write(b"]")
    elif isinstance(v, bool):
        out.write(b"true" if v else b"false")
    elif isinstance(v, (int, float)):
        if isinstance(v, int):
            out.write(str(v).encode("latin1"))
        else:
            # limit precision
            s = f"{v:.6f}".rstrip("0").rstrip(".")
            if s == "":
                s = "0"
            out.write(s.encode("latin1"))
    elif isinstance(v, bytes):
        # write as literal string
        try:
            s = v.decode("latin1")
        except Exception:
            s = ""
        out.write(_escape_pdf_string(s))
    elif isinstance(v, str):
        # Could be name starting with '/' or a literal string
        if v.startswith("/"):
            _write_name(out, v)
        else:
            out.write(_escape_pdf_string(v))
    elif v is None:
        out.write(b"null")
    else:
        # fallback string
        out.write(_escape_pdf_string(str(v)))


def _write_dict(out, d):
    out.write(b"<<")
    first = True
    for k, v in d.items():
        out.write(b" ")
        _write_name(out, k)
        out.write(b" ")
        # if stream dict (has __stream__), omit it here
        if isinstance(v, dict) and "__stream__" in v:
            sub = dict(v)
            sub.pop("__stream__", None)
            _write_dict(out, sub)
        else:
            _write_value(out, v)
    out.write(b" >>")


def _write_indirect_object(out, objnum, gen, value):
    out.write(f"{objnum} {gen} obj\n".encode("latin1"))
    if isinstance(value, dict) and "__stream__" in value:
        # write the dict without stream first
        d = dict(value)
        stream = d.pop("__stream__", b"")
        d["/Length"] = len(stream)
        _write_dict(out, d)
        out.write(b"\nstream\n")
        out.write(stream)
        out.write(b"\nendstream\n")
    else:
        _write_value(out, value)
        out.write(b"\n")
    out.write(b"endobj\n")