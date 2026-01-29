import decimal

class PdfObject:
    def get_object(self):
        return self

class NullObject(PdfObject):
    def write_to_stream(self, stream, encryption_key):
        stream.write(b"null")

class BooleanObject(PdfObject):
    def __init__(self, value):
        self.value = bool(value)

    def __bool__(self):
        return self.value

    def write_to_stream(self, stream, encryption_key):
        stream.write(b"true" if self.value else b"false")

class ArrayObject(list, PdfObject):
    def write_to_stream(self, stream, encryption_key):
        stream.write(b"[")
        for data in self:
            stream.write(b" ")
            data.write_to_stream(stream, encryption_key)
        stream.write(b" ]")

class IndirectObject(PdfObject):
    def __init__(self, idnum, generation, pdf):
        self.idnum = idnum
        self.generation = generation
        self.pdf = pdf

    def get_object(self):
        return self.pdf.get_object(self)

    def write_to_stream(self, stream, encryption_key):
        stream.write(f"{self.idnum} {self.generation} R".encode("ascii"))

    def __repr__(self):
        return f"IndirectObject({self.idnum}, {self.generation})"

class DictionaryObject(dict, PdfObject):
    def raw_get(self, key):
        return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        if not isinstance(key, PdfObject):
            key = NameObject(key)
        return dict.__setitem__(self, key, value)

    def __getitem__(self, key):
        val = dict.__getitem__(self, key)
        if isinstance(val, IndirectObject):
            return val.get_object()
        return val

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def write_to_stream(self, stream, encryption_key):
        stream.write(b"<<\n")
        for key, value in self.items():
            key.write_to_stream(stream, encryption_key)
            stream.write(b" ")
            value.write_to_stream(stream, encryption_key)
            stream.write(b"\n")
        stream.write(b">>")

class StreamObject(DictionaryObject):
    def __init__(self):
        super().__init__()
        self._data = b""

    def set_data(self, data):
        self._data = data

    def get_data(self):
        return self._data

    def write_to_stream(self, stream, encryption_key):
        self[NameObject("/Length")] = NumberObject(len(self._data))
        super().write_to_stream(stream, encryption_key)
        stream.write(b"\nstream\n")
        if encryption_key:
            # Simple encryption handling would go here, but for this scope
            # we assume data is already encrypted or handled by the writer logic
            # if it's a fresh stream.
            # For copy operations, we write raw data.
            stream.write(self._data)
        else:
            stream.write(self._data)
        stream.write(b"\nendstream")

class NameObject(str, PdfObject):
    def write_to_stream(self, stream, encryption_key):
        stream.write(self.encode("ascii"))

class NumberObject(PdfObject):
    def __init__(self, value):
        self.value = value

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def write_to_stream(self, stream, encryption_key):
        stream.write(str(self.value).encode("ascii"))

class TextStringObject(str, PdfObject):
    def write_to_stream(self, stream, encryption_key):
        # Basic escaping
        out = self.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream.write(f"({out})".encode("latin-1")) # Simplified encoding

class ByteStringObject(bytes, PdfObject):
    def write_to_stream(self, stream, encryption_key):
        stream.write(b"<")
        stream.write(self.hex().upper().encode("ascii"))
        stream.write(b">")

def create_string_object(string):
    if isinstance(string, str):
        return TextStringObject(string)
    elif isinstance(string, bytes):
        return ByteStringObject(string)
    raise TypeError("String must be str or bytes")