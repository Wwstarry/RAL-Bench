import collections

# --- Helper Functions ---

def _int_to_synchsafe(val):
    """Converts an integer to a 4-byte synchsafe integer."""
    b1 = (val >> 21) & 0x7F
    b2 = (val >> 14) & 0x7F
    b3 = (val >> 7) & 0x7F
    b4 = val & 0x7F
    return bytes([b1, b2, b3, b4])

def _synchsafe_to_int(b):
    """Converts a 4-byte synchsafe integer to a regular integer."""
    return (b[0] << 21) | (b[1] << 14) | (b[2] << 7) | b[3]

_ENCODING_MAP = {
    0: ('iso-8859-1', b'\x00'),
    1: ('utf-16', b'\x00\x00'),
    2: ('utf-16-be', b'\x00\x00'),
    3: ('utf-8', b'\x00'),
}

def _get_encoding_name(byte):
    return _ENCODING_MAP.get(byte, ('iso-8859-1', b'\x00'))[0]

def _get_encoding_terminator(byte):
    return _ENCODING_MAP.get(byte, ('iso-8859-1', b'\x00'))[1]

# --- Frame Base Class ---

class Frame:
    def __init__(self, id):
        self.id = id

    def _render(self, payload):
        """Creates the full frame binary data (header + payload)."""
        size = len(payload)
        flags = b'\x00\x00'
        return self.id.encode('latin1') + size.to_bytes(4, 'big') + flags + payload

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

# --- Frame Classes ---

def _create_text_frame(frame_id):
    """A factory to create simple text frame classes."""
    class TextFrame(Frame):
        def __init__(self, encoding=3, text=""):
            super().__init__(frame_id)
            self.encoding = encoding
            self.text = str(text)

        def serialize(self):
            name = _get_encoding_name(self.encoding)
            payload = self.encoding.to_bytes(1, 'big') + self.text.encode(name, errors='replace')
            return self._render(payload)

        @classmethod
        def deserialize(cls, id, data):
            encoding = data[0]
            name = _get_encoding_name(encoding)
            text = data[1:].decode(name, errors='replace').rstrip('\x00')
            return cls(encoding=encoding, text=text)

    TextFrame.__name__ = frame_id
    return TextFrame

TIT2 = _create_text_frame('TIT2')
TPE1 = _create_text_frame('TPE1')
TALB = _create_text_frame('TALB')
TRCK = _create_text_frame('TRCK')
TDRC = _create_text_frame('TDRC')
TCON = _create_text_frame('TCON')

class COMM(Frame):
    def __init__(self, encoding=3, lang='eng', desc='', text=''):
        super().__init__('COMM')
        self.encoding = encoding
        self.lang = lang
        self.desc = desc
        self.text = text

    def serialize(self):
        name = _get_encoding_name(self.encoding)
        terminator = _get_encoding_terminator(self.encoding)
        payload = (
            self.encoding.to_bytes(1, 'big') +
            self.lang.encode('latin1')[:3] +
            self.desc.encode(name, errors='replace') + terminator +
            self.text.encode(name, errors='replace')
        )
        return self._render(payload)

    @classmethod
    def deserialize(cls, id, data):
        encoding = data[0]
        name = _get_encoding_name(encoding)
        terminator = _get_encoding_terminator(encoding)
        lang = data[1:4].decode('latin1')
        
        parts = data[4:].split(terminator, 1)
        desc = parts[0].decode(name, errors='replace')
        text = parts[1].decode(name, errors='replace') if len(parts) > 1 else ''
        
        return cls(encoding=encoding, lang=lang, desc=desc, text=text)

class APIC(Frame):
    def __init__(self, encoding=3, mime='image/jpeg', type=3, desc='', data=b''):
        super().__init__('APIC')
        self.encoding = encoding
        self.mime = mime
        self.type = type
        self.desc = desc
        self.data = data

    def serialize(self):
        name = _get_encoding_name(self.encoding)
        terminator = _get_encoding_terminator(self.encoding)
        payload = (
            self.encoding.to_bytes(1, 'big') +
            self.mime.encode('latin1') + b'\x00' +
            self.type.to_bytes(1, 'big') +
            self.desc.encode(name, errors='replace') + terminator +
            self.data
        )
        return self._render(payload)

    @classmethod
    def deserialize(cls, id, data):
        encoding = data[0]
        name = _get_encoding_name(encoding)
        terminator = _get_encoding_terminator(encoding)
        
        mime_end = data.find(b'\x00', 1)
        mime = data[1:mime_end].decode('latin1')
        
        pic_type = data[mime_end + 1]
        desc_start = mime_end + 2
        
        parts = data[desc_start:].split(terminator, 1)
        desc = parts[0].decode(name, errors='replace')
        pic_data = parts[1] if len(parts) > 1 else b''
        
        return cls(encoding=encoding, mime=mime, type=pic_type, desc=desc, data=pic_data)

# --- ID3 Class ---

class ID3:
    _FRAME_CLASSES = {
        'TIT2': TIT2, 'TPE1': TPE1, 'TALB': TALB, 'TRCK': TRCK,
        'TDRC': TDRC, 'TCON': TCON, 'COMM': COMM, 'APIC': APIC,
    }

    def __init__(self, filename=None):
        self.filename = filename
        self.frames = collections.defaultdict(list)
        self._audio_data = b''
        if filename:
            try:
                self.load(filename)
            except (FileNotFoundError, IOError):
                pass

    def load(self, filename):
        with open(filename, 'rb') as f:
            header = f.read(10)
            if len(header) == 10 and header[:3] == b'ID3':
                size = _synchsafe_to_int(header[6:])
                tag_data = f.read(size)
                self._parse_frames(tag_data)
                self._audio_data = f.read()
            else:
                f.seek(0)
                self._audio_data = f.read()

    def _parse_frames(self, tag_data):
        offset = 0
        while offset < len(tag_data):
            if tag_data[offset:offset+1] == b'\x00':
                break

            if offset + 10 > len(tag_data):
                break

            frame_header = tag_data[offset:offset+10]
            frame_id = frame_header[:4].decode('latin1', errors='ignore')
            frame_size = int.from_bytes(frame_header[4:8], 'big')
            
            offset += 10
            if offset + frame_size > len(tag_data) or frame_size == 0:
                break

            frame_data = tag_data[offset:offset+frame_size]
            offset += frame_size

            if frame_id in self._FRAME_CLASSES:
                cls = self._FRAME_CLASSES[frame_id]
                try:
                    frame = cls.deserialize(frame_id, frame_data)
                    self.add(frame)
                except Exception:
                    pass

    def save(self, filename=None):
        target_filename = filename or self.filename
        if not target_filename:
            raise ValueError("No filename specified to save to")

        all_frames_data = b''
        for frame_id in sorted(self.frames.keys()):
            for frame in self.frames[frame_id]:
                all_frames_data += frame.serialize()
        
        tag_size = len(all_frames_data)
        
        with open(target_filename, 'wb') as f:
            if tag_size > 0:
                header = b'ID3\x03\x00\x00' + _int_to_synchsafe(tag_size)
                f.write(header)
                f.write(all_frames_data)
            f.write(self._audio_data)

    def add(self, frame):
        self.frames[frame.id].append(frame)

    def getall(self, key):
        return self.frames.get(key, [])

    def setall(self, key, frames):
        self.frames[key] = list(frames)

    def delall(self, key):
        if key in self.frames:
            del self.frames[key]

    def __getitem__(self, key):
        try:
            return self.frames[key][0]
        except (KeyError, IndexError):
            raise KeyError(f"No frame with ID '{key}'")

    def __setitem__(self, key, frame):
        self.frames[key] = [frame]

    def __delitem__(self, key):
        if key in self.frames:
            self.delall(key)
        else:
            raise KeyError(key)