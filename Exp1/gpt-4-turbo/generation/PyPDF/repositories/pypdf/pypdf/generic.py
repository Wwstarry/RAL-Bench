import re
import struct

class PdfObject:
    pass

class IndirectObject(PdfObject):
    def __init__(self, objnum, gennum, pdf):
        self.idnum = objnum
        self.gennum = gennum
        self.pdf = pdf

    def get_object(self):
        return self.pdf._get_object(self.idnum, self.gennum)

class DictionaryObject(dict, PdfObject):
    def __getitem__(self, key):
        return dict.__getitem__(self, key)

    def get(self, key, default=None):
        return dict.get(self, key, default)

class ArrayObject(list, PdfObject):
    pass

class NameObject(str, PdfObject):
    pass

class NumberObject(float, PdfObject):
    pass

class ByteStringObject(bytes, PdfObject):
    pass

class TextStringObject(str, PdfObject):
    pass

class NullObject(PdfObject):
    pass

def decode_pdf_string(s):
    if isinstance(s, bytes):
        try:
            return s.decode("utf-8")
        except Exception:
            return s.decode("latin1")
    return s

def encode_pdf_string(s):
    if isinstance(s, str):
        return s.encode("utf-8")
    return s

def read_until_whitespace(stream):
    result = b""
    while True:
        c = stream.read(1)
        if not c or c in b" \t\n\r\f\x00":
            break
        result += c
    return result

def skip_whitespace(stream):
    while True:
        c = stream.read(1)
        if not c or c not in b" \t\n\r\f\x00":
            stream.seek(-1, 1)
            break

def read_line(stream):
    line = b""
    while True:
        c = stream.read(1)
        if not c or c == b"\n":
            break
        if c == b"\r":
            c2 = stream.read(1)
            if c2 != b"\n":
                stream.seek(-1, 1)
            break
        line += c
    return line

def parse_indirect_object(stream, pdf):
    pos = stream.tell()
    objnum = int(read_until_whitespace(stream))
    skip_whitespace(stream)
    gennum = int(read_until_whitespace(stream))
    skip_whitespace(stream)
    word = read_until_whitespace(stream)
    if word != b"obj":
        raise ValueError("Expected 'obj'")
    obj = parse_object(stream, pdf)
    # skip 'endobj'
    while True:
        line = read_line(stream)
        if line.strip() == b"endobj":
            break
    return objnum, gennum, obj

def parse_object(stream, pdf):
    skip_whitespace(stream)
    c = stream.read(1)
    if not c:
        return None
    if c == b"<":
        c2 = stream.read(1)
        if c2 == b"<":
            # dictionary
            d = DictionaryObject()
            while True:
                skip_whitespace(stream)
                peek = stream.read(1)
                if peek == b">":
                    peek2 = stream.read(1)
                    if peek2 == b">":
                        break
                    else:
                        stream.seek(-1, 1)
                else:
                    stream.seek(-1, 1)
                key = parse_object(stream, pdf)
                val = parse_object(stream, pdf)
                d[key] = val
            return d
        else:
            # hex string
            s = b""
            while True:
                c = stream.read(1)
                if c == b">":
                    break
                s += c
            return ByteStringObject(bytes.fromhex(s.decode()))
    elif c == b"/":
        name = read_until_whitespace(stream)
        return NameObject("/" + name.decode())
    elif c == b"(":
        # literal string
        s = b""
        depth = 1
        while depth > 0:
            c = stream.read(1)
            if c == b"(":
                depth += 1
            elif c == b")":
                depth -= 1
                if depth == 0:
                    break
            elif c == b"\\":
                c2 = stream.read(1)
                s += c2
            else:
                s += c
        return TextStringObject(decode_pdf_string(s))
    elif c in b"0123456789.-":
        stream.seek(-1, 1)
        num = read_until_whitespace(stream)
        if b"." in num:
            return NumberObject(float(num))
        else:
            return NumberObject(int(num))
    elif c == b"[":
        arr = ArrayObject()
        while True:
            skip_whitespace(stream)
            peek = stream.read(1)
            if peek == b"]":
                break
            else:
                stream.seek(-1, 1)
                obj = parse_object(stream, pdf)
                arr.append(obj)
        return arr
    elif c == b"n":
        # null
        rest = stream.read(3)
        if rest == b"ull":
            return NullObject()
        else:
            raise ValueError("Invalid null object")
    elif c == b"t":
        # true
        rest = stream.read(3)
        if rest == b"rue":
            return True
        else:
            raise ValueError("Invalid true object")
    elif c == b"f":
        # false
        rest = stream.read(4)
        if rest == b"alse":
            return False
        else:
            raise ValueError("Invalid false object")
    elif c in b"R":
        # indirect reference
        return None
    else:
        return None