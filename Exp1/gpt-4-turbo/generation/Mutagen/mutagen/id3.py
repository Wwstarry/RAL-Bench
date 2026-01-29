import struct
import os

# --- Frame classes ---

class ID3Frame(object):
    def __init__(self, frame_id):
        self.frame_id = frame_id

    def get_id(self):
        return self.frame_id

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

class TIT2(ID3Frame):
    def __init__(self, encoding, text):
        super().__init__("TIT2")
        self.encoding = encoding
        self.text = text

    def render(self):
        data = struct.pack("B", self.encoding)
        if self.encoding == 0:
            data += self.text.encode("latin1")
        else:
            data += self.text.encode("utf-8")
        return data

    @classmethod
    def parse(cls, data):
        encoding = data[0]
        text = data[1:]
        if encoding == 0:
            text = text.decode("latin1")
        else:
            text = text.decode("utf-8")
        return TIT2(encoding, text)

class TPE1(ID3Frame):
    def __init__(self, encoding, text):
        super().__init__("TPE1")
        self.encoding = encoding
        self.text = text

    def render(self):
        data = struct.pack("B", self.encoding)
        if self.encoding == 0:
            data += self.text.encode("latin1")
        else:
            data += self.text.encode("utf-8")
        return data

    @classmethod
    def parse(cls, data):
        encoding = data[0]
        text = data[1:]
        if encoding == 0:
            text = text.decode("latin1")
        else:
            text = text.decode("utf-8")
        return TPE1(encoding, text)

class COMM(ID3Frame):
    def __init__(self, encoding, lang, desc, text):
        super().__init__("COMM")
        self.encoding = encoding
        self.lang = lang
        self.desc = desc
        self.text = text

    def render(self):
        data = struct.pack("B", self.encoding)
        data += self.lang.encode("latin1")
        if self.encoding == 0:
            data += self.desc.encode("latin1") + b"\x00"
            data += self.text.encode("latin1")
        else:
            data += self.desc.encode("utf-8") + b"\x00"
            data += self.text.encode("utf-8")
        return data

    @classmethod
    def parse(cls, data):
        encoding = data[0]
        lang = data[1:4].decode("latin1")
        rest = data[4:]
        if encoding == 0:
            desc, text = rest.split(b"\x00", 1)
            desc = desc.decode("latin1")
            text = text.decode("latin1")
        else:
            desc, text = rest.split(b"\x00", 1)
            desc = desc.decode("utf-8")
            text = text.decode("utf-8")
        return COMM(encoding, lang, desc, text)

class APIC(ID3Frame):
    def __init__(self, encoding, mime, type_, desc, data):
        super().__init__("APIC")
        self.encoding = encoding
        self.mime = mime
        self.type = type_
        self.desc = desc
        self.data = data

    def render(self):
        data = struct.pack("B", self.encoding)
        data += self.mime.encode("latin1") + b"\x00"
        data += struct.pack("B", self.type)
        if self.encoding == 0:
            data += self.desc.encode("latin1") + b"\x00"
        else:
            data += self.desc.encode("utf-8") + b"\x00"
        data += self.data
        return data

    @classmethod
    def parse(cls, data):
        encoding = data[0]
        rest = data[1:]
        mime_end = rest.find(b"\x00")
        mime = rest[:mime_end].decode("latin1")
        rest = rest[mime_end+1:]
        type_ = rest[0]
        rest = rest[1:]
        desc_end = rest.find(b"\x00")
        if encoding == 0:
            desc = rest[:desc_end].decode("latin1")
        else:
            desc = rest[:desc_end].decode("utf-8")
        img_data = rest[desc_end+1:]
        return APIC(encoding, mime, type_, desc, img_data)

# --- ID3 tag handling ---

def _syncsafe(size):
    # Convert integer to syncsafe (4 bytes, 7 bits each)
    b1 = (size >> 21) & 0x7F
    b2 = (size >> 14) & 0x7F
    b3 = (size >> 7) & 0x7F
    b4 = size & 0x7F
    return bytes([b1, b2, b3, b4])

def _unsyncsafe(b):
    # Convert syncsafe bytes to integer
    return ((b[0] & 0x7F) << 21) | ((b[1] & 0x7F) << 14) | ((b[2] & 0x7F) << 7) | (b[3] & 0x7F)

_FRAME_CLASSES = {
    "TIT2": TIT2,
    "TPE1": TPE1,
    "COMM": COMM,
    "APIC": APIC,
}

class ID3(object):
    def __init__(self, filename=None):
        self._frames = []
        self._filename = filename
        if filename is not None:
            self._load(filename)

    def _load(self, filename):
        with open(filename, "rb") as f:
            header = f.read(10)
            if len(header) < 10 or header[:3] != b"ID3":
                return
            version = header[3]
            flags = header[5]
            tag_size = _unsyncsafe(header[6:10])
            tag_data = f.read(tag_size)
            offset = 0
            while offset + 10 <= len(tag_data):
                frame_id = tag_data[offset:offset+4].decode("latin1")
                frame_size = struct.unpack(">I", tag_data[offset+4:offset+8])[0]
                frame_flags = tag_data[offset+8:offset+10]
                frame_data = tag_data[offset+10:offset+10+frame_size]
                offset += 10 + frame_size
                if frame_id.strip("\x00") == "":
                    continue
                cls = _FRAME_CLASSES.get(frame_id)
                if cls:
                    try:
                        frame = cls.parse(frame_data)
                        self._frames.append(frame)
                    except Exception:
                        pass
                else:
                    # Store unknown frames as raw
                    self._frames.append((frame_id, frame_data))

    def add(self, frame):
        self._frames.append(frame)

    def __getitem__(self, frame_id):
        for f in self._frames:
            if isinstance(f, ID3Frame) and f.frame_id == frame_id:
                return f
        raise KeyError(frame_id)

    def getall(self, frame_id):
        return [f for f in self._frames if isinstance(f, ID3Frame) and f.frame_id == frame_id]

    def delall(self, frame_id):
        self._frames = [f for f in self._frames if not (isinstance(f, ID3Frame) and f.frame_id == frame_id)]

    def setall(self, frame_id, frames):
        self.delall(frame_id)
        for f in frames:
            self.add(f)

    def save(self, filename=None):
        if filename is None:
            filename = self._filename
        if filename is None:
            raise ValueError("No filename specified")
        tag_bytes = self._render()
        # Write tag-only file if no audio
        with open(filename, "rb") as f:
            file_data = f.read()
        if file_data[:3] == b"ID3":
            # Replace existing tag
            # Find where tag ends
            tag_size = _unsyncsafe(file_data[6:10])
            tag_end = 10 + tag_size
            rest = file_data[tag_end:]
            with open(filename, "wb") as f:
                f.write(tag_bytes)
                f.write(rest)
        else:
            # Write tag-only file
            with open(filename, "wb") as f:
                f.write(tag_bytes)

    def _render(self):
        frames_data = b""
        for f in self._frames:
            if isinstance(f, ID3Frame):
                frame_id = f.frame_id.encode("latin1")
                frame_body = f.render()
                frame_size = struct.pack(">I", len(frame_body))
                frame_flags = b"\x00\x00"
                frames_data += frame_id + frame_size + frame_flags + frame_body
            else:
                # Unknown frame: (frame_id, raw_data)
                frame_id = f[0].encode("latin1")
                frame_body = f[1]
                frame_size = struct.pack(">I", len(frame_body))
                frame_flags = b"\x00\x00"
                frames_data += frame_id + frame_size + frame_flags + frame_body
        tag_size = len(frames_data)
        header = b"ID3" + b"\x03\x00" + b"\x00" + _syncsafe(tag_size)
        return header + frames_data