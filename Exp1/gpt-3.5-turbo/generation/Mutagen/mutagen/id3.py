import io
import struct

class ID3:
    def __init__(self, fileobj_or_path=None):
        self._frames = []
        self._frame_map = {}  # frame_id -> list of frames
        self._file_path = None
        if fileobj_or_path is not None:
            if isinstance(fileobj_or_path, str):
                self._file_path = fileobj_or_path
                with open(fileobj_or_path, "rb") as f:
                    self._read(f)
            else:
                self._read(fileobj_or_path)

    def _read(self, fileobj):
        # Read ID3v2 header if present
        fileobj.seek(0)
        header = fileobj.read(10)
        if len(header) < 10 or header[0:3] != b"ID3":
            # No ID3 tag found, empty tag
            return
        # Parse header
        version_major = header[3]
        version_minor = header[4]
        flags = header[5]
        size = self._syncsafe_to_size(header[6:10])
        tag_data = fileobj.read(size)
        self._frames = []
        self._frame_map = {}
        pos = 0
        while pos + 10 <= len(tag_data):
            frame_header = tag_data[pos:pos+10]
            frame_id = frame_header[0:4].decode("latin1")
            if frame_id.strip('\x00') == '':
                break
            frame_size = struct.unpack(">I", frame_header[4:8])[0]
            frame_flags = frame_header[8:10]
            frame_data = tag_data[pos+10:pos+10+frame_size]
            pos += 10 + frame_size
            frame = self._parse_frame(frame_id, frame_data)
            if frame is not None:
                self.add(frame)

    def _syncsafe_to_size(self, b):
        # 4 bytes syncsafe integer
        size = 0
        for byte in b:
            size = (size << 7) | (byte & 0x7F)
        return size

    def _size_to_syncsafe(self, size):
        b = bytearray(4)
        for i in range(3, -1, -1):
            b[i] = size & 0x7F
            size >>= 7
        return bytes(b)

    def _parse_frame(self, frame_id, data):
        # Only parse frames we know
        if frame_id == "TIT2":
            return TIT2.from_bytes(data)
        elif frame_id == "TPE1":
            return TPE1.from_bytes(data)
        elif frame_id == "COMM":
            return COMM.from_bytes(data)
        elif frame_id == "APIC":
            return APIC.from_bytes(data)
        else:
            # Unknown frame, ignore
            return None

    def add(self, frame):
        self._frames.append(frame)
        self._frame_map.setdefault(frame.FrameID, []).append(frame)

    def __getitem__(self, frame_id):
        frames = self._frame_map.get(frame_id)
        if not frames:
            raise KeyError(frame_id)
        return frames[0]

    def getall(self, frame_id):
        return list(self._frame_map.get(frame_id, []))

    def delall(self, frame_id):
        frames = self._frame_map.pop(frame_id, [])
        if not frames:
            return
        self._frames = [f for f in self._frames if f.FrameID != frame_id]

    def setall(self, frame_id, frames):
        # Remove old frames with frame_id
        self.delall(frame_id)
        for frame in frames:
            self.add(frame)

    def save(self, path=None):
        if path is None:
            if self._file_path is None:
                raise ValueError("No file path specified for saving")
            path = self._file_path
        # Build tag data
        frames_data = b"".join(frame.render() for frame in self._frames)
        size = len(frames_data)
        header = b"ID3" + bytes([3, 0, 0]) + self._size_to_syncsafe(size)
        with open(path, "wb") as f:
            f.write(header)
            f.write(frames_data)
            # No audio data, tag-only file

class Frame:
    FrameID = None

    def render(self):
        # Returns bytes of frame header + frame data
        data = self._render_data()
        size = len(data)
        header = self.FrameID.encode("latin1") + struct.pack(">I", size) + b"\x00\x00"
        return header + data

    def _render_data(self):
        raise NotImplementedError

class TextFrame(Frame):
    def __init__(self, encoding, text=None):
        self.encoding = encoding
        if text is None:
            self.text = []
        elif isinstance(text, list):
            self.text = text
        else:
            self.text = [text]

    @classmethod
    def from_bytes(cls, data):
        if len(data) == 0:
            return cls(encoding=3, text=[])
        encoding = data[0]
        raw_text = data[1:]
        texts = cls._decode_texts(encoding, raw_text)
        return cls(encoding, texts)

    @staticmethod
    def _decode_texts(encoding, raw_text):
        # Text frames may contain multiple strings separated by \x00 or \x00\x00 depending on encoding
        if encoding == 0:
            # ISO-8859-1, strings separated by \x00
            texts = raw_text.split(b'\x00')
            return [t.decode('latin1') for t in texts if t != b'']
        elif encoding == 1:
            # UTF-16 with BOM, strings separated by \x00\x00
            try:
                text = raw_text.decode('utf-16')
            except UnicodeDecodeError:
                # fallback
                text = raw_text.decode('utf-16le', errors='replace')
            texts = text.split('\x00')
            return [t for t in texts if t != '']
        elif encoding == 2:
            # UTF-16BE without BOM, separated by \x00\x00
            try:
                text = raw_text.decode('utf-16-be')
            except UnicodeDecodeError:
                text = raw_text.decode('utf-16-be', errors='replace')
            texts = text.split('\x00')
            return [t for t in texts if t != '']
        elif encoding == 3:
            # UTF-8, separated by \x00
            texts = raw_text.split(b'\x00')
            return [t.decode('utf-8') for t in texts if t != b'']
        else:
            # Unknown encoding, treat as latin1
            texts = raw_text.split(b'\x00')
            return [t.decode('latin1') for t in texts if t != b'']

    def _render_data(self):
        # Encode text list into bytes with encoding prefix
        if self.encoding == 0:
            # latin1, separated by \x00
            encoded = b'\x00'.join(t.encode('latin1') for t in self.text)
            return bytes([0]) + encoded
        elif self.encoding == 1:
            # UTF-16 with BOM, separated by \x00\x00
            encoded = '\x00'.join(self.text).encode('utf-16')
            return bytes([1]) + encoded
        elif self.encoding == 2:
            # UTF-16BE without BOM, separated by \x00\x00
            encoded = '\x00'.join(self.text).encode('utf-16-be')
            return bytes([2]) + encoded
        elif self.encoding == 3:
            # UTF-8, separated by \x00
            encoded = b'\x00'.join(t.encode('utf-8') for t in self.text)
            return bytes([3]) + encoded
        else:
            # fallback latin1
            encoded = b'\x00'.join(t.encode('latin1') for t in self.text)
            return bytes([0]) + encoded

class TIT2(TextFrame):
    FrameID = "TIT2"

class TPE1(TextFrame):
    FrameID = "TPE1"

class COMM(Frame):
    FrameID = "COMM"

    def __init__(self, encoding, lang, desc, text):
        self.encoding = encoding
        self.lang = lang
        self.desc = desc
        if isinstance(text, list):
            self.text = text
        else:
            self.text = [text]

    @classmethod
    def from_bytes(cls, data):
        if len(data) < 4:
            # invalid COMM frame
            return cls(3, 'eng', '', [])
        encoding = data[0]
        lang = data[1:4].decode('latin1')
        rest = data[4:]
        # description and text separated by null terminator(s)
        # description is encoded with encoding, terminated by null
        # text is encoded with encoding, can be multiple strings separated by nulls
        # decode description
        if encoding == 0:
            # latin1, null terminator is b'\x00'
            parts = rest.split(b'\x00', 1)
            if len(parts) == 2:
                desc_bytes, text_bytes = parts
            else:
                desc_bytes = rest
                text_bytes = b''
            desc = desc_bytes.decode('latin1')
            texts = text_bytes.split(b'\x00')
            texts = [t.decode('latin1') for t in texts if t != b'']
        elif encoding == 1:
            # UTF-16 with BOM, null terminator is b'\x00\x00'
            # find null terminator for desc
            # decode with utf-16
            # split rest accordingly
            # find first null terminator (two zero bytes)
            # We decode as utf-16-le or utf-16-be depending on BOM
            # We'll decode entire rest and then split by \x00
            try:
                rest_text = rest.decode('utf-16')
            except UnicodeDecodeError:
                rest_text = rest.decode('utf-16le', errors='replace')
            parts = rest_text.split('\x00', 1)
            if len(parts) == 2:
                desc, text_str = parts
            else:
                desc = rest_text
                text_str = ''
            texts = [t for t in text_str.split('\x00') if t != '']
        elif encoding == 2:
            # UTF-16BE without BOM
            try:
                rest_text = rest.decode('utf-16-be')
            except UnicodeDecodeError:
                rest_text = rest.decode('utf-16-be', errors='replace')
            parts = rest_text.split('\x00', 1)
            if len(parts) == 2:
                desc, text_str = parts
            else:
                desc = rest_text
                text_str = ''
            texts = [t for t in text_str.split('\x00') if t != '']
        elif encoding == 3:
            # UTF-8
            parts = rest.split(b'\x00', 1)
            if len(parts) == 2:
                desc_bytes, text_bytes = parts
            else:
                desc_bytes = rest
                text_bytes = b''
            desc = desc_bytes.decode('utf-8')
            texts = text_bytes.split(b'\x00')
            texts = [t.decode('utf-8') for t in texts if t != b'']
        else:
            # fallback latin1
            parts = rest.split(b'\x00', 1)
            if len(parts) == 2:
                desc_bytes, text_bytes = parts
            else:
                desc_bytes = rest
                text_bytes = b''
            desc = desc_bytes.decode('latin1')
            texts = text_bytes.split(b'\x00')
            texts = [t.decode('latin1') for t in texts if t != b'']
        return cls(encoding, lang, desc, texts)

    def _render_data(self):
        # encode description and text with encoding
        if self.encoding == 0:
            desc_bytes = self.desc.encode('latin1') + b'\x00'
            text_bytes = b'\x00'.join(t.encode('latin1') for t in self.text)
            return bytes([0]) + self.lang.encode('latin1') + desc_bytes + text_bytes
        elif self.encoding == 1:
            desc_bytes = self.desc + '\x00'
            desc_bytes = desc_bytes.encode('utf-16')
            text_bytes = '\x00'.join(self.text).encode('utf-16')
            return bytes([1]) + self.lang.encode('latin1') + desc_bytes + text_bytes
        elif self.encoding == 2:
            desc_bytes = self.desc + '\x00'
            desc_bytes = desc_bytes.encode('utf-16-be')
            text_bytes = '\x00'.join(self.text).encode('utf-16-be')
            return bytes([2]) + self.lang.encode('latin1') + desc_bytes + text_bytes
        elif self.encoding == 3:
            desc_bytes = self.desc.encode('utf-8') + b'\x00'
            text_bytes = b'\x00'.join(t.encode('utf-8') for t in self.text)
            return bytes([3]) + self.lang.encode('latin1') + desc_bytes + text_bytes
        else:
            desc_bytes = self.desc.encode('latin1') + b'\x00'
            text_bytes = b'\x00'.join(t.encode('latin1') for t in self.text)
            return bytes([0]) + self.lang.encode('latin1') + desc_bytes + text_bytes

class APIC(Frame):
    FrameID = "APIC"

    def __init__(self, encoding, mime, type, desc, data):
        self.encoding = encoding
        self.mime = mime
        self.type = type
        self.desc = desc
        self.data = data

    @classmethod
    def from_bytes(cls, data):
        if len(data) < 4:
            # invalid APIC frame
            return cls(3, '', 0, '', b'')
        encoding = data[0]
        rest = data[1:]
        # mime string terminated by \x00
        try:
            mime_end = rest.index(0)
        except ValueError:
            # no null terminator, invalid
            mime_end = len(rest)
        mime = rest[:mime_end].decode('latin1')
        rest2 = rest[mime_end+1:]
        if len(rest2) < 1:
            pic_type = 0
            desc = ''
            pic_data = b''
            return cls(encoding, mime, pic_type, desc, pic_data)
        pic_type = rest2[0]
        rest3 = rest2[1:]
        # description terminated by null depending on encoding
        if encoding == 0:
            # latin1, null terminator b'\x00'
            try:
                desc_end = rest3.index(0)
            except ValueError:
                desc_end = len(rest3)
            desc = rest3[:desc_end].decode('latin1')
            pic_data = rest3[desc_end+1:]
        elif encoding == 1:
            # UTF-16 with BOM, null terminator b'\x00\x00'
            # find null terminator
            desc = ''
            pic_data = b''
            # decode utf-16 string until null terminator
            # find null terminator in bytes
            # We search for b'\x00\x00' in rest3
            null_pos = -1
            for i in range(0, len(rest3)-1, 2):
                if rest3[i] == 0 and rest3[i+1] == 0:
                    null_pos = i
                    break
            if null_pos == -1:
                desc_bytes = rest3
                pic_data = b''
            else:
                desc_bytes = rest3[:null_pos]
                pic_data = rest3[null_pos+2:]
            try:
                desc = desc_bytes.decode('utf-16')
            except UnicodeDecodeError:
                desc = desc_bytes.decode('utf-16le', errors='replace')
        elif encoding == 2:
            # UTF-16BE without BOM, null terminator b'\x00\x00'
            null_pos = -1
            for i in range(0, len(rest3)-1, 2):
                if rest3[i] == 0 and rest3[i+1] == 0:
                    null_pos = i
                    break
            if null_pos == -1:
                desc_bytes = rest3
                pic_data = b''
            else:
                desc_bytes = rest3[:null_pos]
                pic_data = rest3[null_pos+2:]
            try:
                desc = desc_bytes.decode('utf-16-be')
            except UnicodeDecodeError:
                desc = desc_bytes.decode('utf-16-be', errors='replace')
        elif encoding == 3:
            # UTF-8, null terminator b'\x00'
            try:
                desc_end = rest3.index(0)
            except ValueError:
                desc_end = len(rest3)
            desc = rest3[:desc_end].decode('utf-8')
            pic_data = rest3[desc_end+1:]
        else:
            # fallback latin1
            try:
                desc_end = rest3.index(0)
            except ValueError:
                desc_end = len(rest3)
            desc = rest3[:desc_end].decode('latin1')
            pic_data = rest3[desc_end+1:]
        return cls(encoding, mime, pic_type, desc, pic_data)

    def _render_data(self):
        # Compose bytes for APIC frame
        if self.encoding == 0:
            desc_bytes = self.desc.encode('latin1') + b'\x00'
        elif self.encoding == 1:
            desc_bytes = (self.desc + '\x00').encode('utf-16')
        elif self.encoding == 2:
            desc_bytes = (self.desc + '\x00').encode('utf-16-be')
        elif self.encoding == 3:
            desc_bytes = self.desc.encode('utf-8') + b'\x00'
        else:
            desc_bytes = self.desc.encode('latin1') + b'\x00'
        return (
            bytes([self.encoding]) +
            self.mime.encode('latin1') + b'\x00' +
            bytes([self.type]) +
            desc_bytes +
            self.data
        )