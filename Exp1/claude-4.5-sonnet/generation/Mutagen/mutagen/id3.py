"""
ID3 - Low-level ID3 tag interface.
"""

import struct
import os


class ID3:
    """
    Low-level ID3 tag container.
    """
    
    def __init__(self, filename=None):
        """
        Create an ID3 instance.
        
        Args:
            filename: Optional path to an MP3 file to load tags from.
        """
        self._filename = filename
        self._frames = {}  # frame_id -> list of frames
        
        if filename and os.path.exists(filename):
            self._load(filename)
    
    def _load(self, filename):
        """Load ID3 tags from a file."""
        with open(filename, 'rb') as f:
            data = f.read()
        
        if len(data) < 10:
            return
        
        # Check for ID3v2 header
        if data[:3] != b'ID3':
            return
        
        # Parse ID3v2 header
        version_major = data[3]
        version_minor = data[4]
        flags = data[5]
        
        # Parse synchsafe size (4 bytes, 7 bits each)
        size = self._decode_synchsafe(data[6:10])
        
        # Parse frames
        offset = 10
        end = 10 + size
        
        while offset < end and offset < len(data):
            if offset + 10 > len(data):
                break
            
            # Check for padding
            if data[offset] == 0:
                break
            
            # Parse frame header
            frame_id = data[offset:offset+4].decode('latin1', errors='ignore')
            
            if version_major >= 4:
                frame_size = self._decode_synchsafe(data[offset+4:offset+8])
            else:
                frame_size = struct.unpack('>I', data[offset+4:offset+8])[0]
            
            frame_flags = struct.unpack('>H', data[offset+8:offset+10])[0]
            
            offset += 10
            
            if offset + frame_size > len(data):
                break
            
            frame_data = data[offset:offset+frame_size]
            offset += frame_size
            
            # Parse frame
            frame = self._parse_frame(frame_id, frame_data)
            if frame:
                if frame_id not in self._frames:
                    self._frames[frame_id] = []
                self._frames[frame_id].append(frame)
    
    def _parse_frame(self, frame_id, data):
        """Parse a frame from raw data."""
        if not data:
            return None
        
        # Text frames
        if frame_id.startswith('T') and frame_id not in ('TXXX',):
            encoding = data[0]
            text_data = data[1:]
            text = self._decode_text(text_data, encoding)
            
            frame_class = _get_text_frame_class(frame_id)
            return frame_class(encoding=encoding, text=text)
        
        # Comment frames
        elif frame_id == 'COMM':
            if len(data) < 4:
                return None
            
            encoding = data[0]
            lang = data[1:4].decode('latin1', errors='ignore')
            
            rest = data[4:]
            # Find null terminator for description
            desc, text_data = self._split_null(rest, encoding)
            text = self._decode_text(text_data, encoding)
            
            return COMM(encoding=encoding, lang=lang, desc=desc, text=text)
        
        # Picture frames
        elif frame_id == 'APIC':
            if len(data) < 2:
                return None
            
            encoding = data[0]
            offset = 1
            
            # Find null terminator for MIME type
            mime_end = data.find(b'\x00', offset)
            if mime_end == -1:
                return None
            
            mime = data[offset:mime_end].decode('latin1', errors='ignore')
            offset = mime_end + 1
            
            if offset >= len(data):
                return None
            
            pic_type = data[offset]
            offset += 1
            
            # Find null terminator for description
            rest = data[offset:]
            desc, pic_data = self._split_null(rest, encoding)
            
            return APIC(encoding=encoding, mime=mime, type=pic_type, 
                       desc=desc, data=pic_data)
        
        return None
    
    def _decode_text(self, data, encoding):
        """Decode text data based on encoding."""
        if encoding == 0:  # Latin-1
            # Split on null terminators
            parts = data.split(b'\x00')
            return [p.decode('latin1', errors='ignore') for p in parts if p]
        elif encoding == 1:  # UTF-16 with BOM
            # Split on UTF-16 null terminators
            parts = []
            current = b''
            i = 0
            while i < len(data):
                if i + 1 < len(data) and data[i:i+2] == b'\x00\x00':
                    if current:
                        parts.append(current.decode('utf-16', errors='ignore'))
                        current = b''
                    i += 2
                else:
                    current += bytes([data[i]])
                    i += 1
            if current:
                parts.append(current.decode('utf-16', errors='ignore'))
            return parts if parts else ['']
        elif encoding == 2:  # UTF-16BE
            parts = data.split(b'\x00\x00')
            return [p.decode('utf-16-be', errors='ignore') for p in parts if p]
        elif encoding == 3:  # UTF-8
            parts = data.split(b'\x00')
            return [p.decode('utf-8', errors='ignore') for p in parts if p]
        else:
            return ['']
    
    def _split_null(self, data, encoding):
        """Split data at null terminator based on encoding."""
        if encoding == 0 or encoding == 3:  # Latin-1 or UTF-8
            null_pos = data.find(b'\x00')
            if null_pos == -1:
                return '', data
            return data[:null_pos].decode('utf-8' if encoding == 3 else 'latin1', 
                                         errors='ignore'), data[null_pos+1:]
        else:  # UTF-16
            # Look for double null
            for i in range(0, len(data) - 1, 2):
                if data[i:i+2] == b'\x00\x00':
                    desc = data[:i].decode('utf-16', errors='ignore')
                    return desc, data[i+2:]
            return '', data
    
    def _decode_synchsafe(self, data):
        """Decode a synchsafe integer."""
        return (data[0] << 21) | (data[1] << 14) | (data[2] << 7) | data[3]
    
    def _encode_synchsafe(self, value):
        """Encode a synchsafe integer."""
        return bytes([
            (value >> 21) & 0x7F,
            (value >> 14) & 0x7F,
            (value >> 7) & 0x7F,
            value & 0x7F
        ])
    
    def add(self, frame):
        """Add a frame to the tag."""
        frame_id = frame.__class__.__name__
        if frame_id not in self._frames:
            self._frames[frame_id] = []
        self._frames[frame_id].append(frame)
    
    def __getitem__(self, frame_id):
        """Get the first frame with the given ID."""
        frames = self._frames.get(frame_id, [])
        if not frames:
            raise KeyError(frame_id)
        return frames[0]
    
    def getall(self, frame_id):
        """Get all frames with the given ID."""
        return self._frames.get(frame_id, [])
    
    def delall(self, frame_id):
        """Delete all frames with the given ID."""
        if frame_id in self._frames:
            del self._frames[frame_id]
    
    def setall(self, frame_id, frames):
        """Set all frames for a given ID."""
        if frames:
            self._frames[frame_id] = list(frames)
        elif frame_id in self._frames:
            del self._frames[frame_id]
    
    def save(self, filename=None):
        """
        Save tags to a file.
        
        Args:
            filename: Optional path to save to. If not provided, saves to
                     the file this instance was loaded from.
        """
        if filename is None:
            filename = self._filename
        
        if filename is None:
            raise ValueError("No filename specified")
        
        # Build ID3v2.4 tag
        frames_data = b''
        
        for frame_id, frames in sorted(self._frames.items()):
            for frame in frames:
                frame_data = self._encode_frame(frame)
                if frame_data:
                    frames_data += frame_data
        
        # Build ID3v2 header
        header = b'ID3'
        header += bytes([4, 0])  # Version 2.4.0
        header += bytes([0])  # Flags
        header += self._encode_synchsafe(len(frames_data))
        
        # Write to file
        tag_data = header + frames_data
        
        # Read existing file if it exists
        audio_data = b''
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                data = f.read()
            
            # Skip existing ID3 tag if present
            if data[:3] == b'ID3':
                if len(data) >= 10:
                    size = self._decode_synchsafe(data[6:10])
                    audio_data = data[10 + size:]
            else:
                audio_data = data
        
        # Write new file
        with open(filename, 'wb') as f:
            f.write(tag_data)
            f.write(audio_data)
    
    def _encode_frame(self, frame):
        """Encode a frame to bytes."""
        frame_id = frame.__class__.__name__
        
        # Encode frame data
        if isinstance(frame, (TIT2, TPE1, TALB, TDRC, TRCK, TCON)):
            data = self._encode_text_frame(frame)
        elif isinstance(frame, COMM):
            data = self._encode_comm_frame(frame)
        elif isinstance(frame, APIC):
            data = self._encode_apic_frame(frame)
        else:
            return None
        
        if not data:
            return None
        
        # Build frame header
        header = frame_id.encode('latin1')
        header += self._encode_synchsafe(len(data))
        header += bytes([0, 0])  # Flags
        
        return header + data
    
    def _encode_text_frame(self, frame):
        """Encode a text frame."""
        encoding = getattr(frame, 'encoding', 3)
        text = getattr(frame, 'text', [])
        
        if not text:
            return None
        
        data = bytes([encoding])
        
        if encoding == 0:  # Latin-1
            data += '\x00'.join(text).encode('latin1', errors='ignore')
        elif encoding == 1:  # UTF-16 with BOM
            data += '\x00\x00'.join(text).encode('utf-16')
        elif encoding == 2:  # UTF-16BE
            data += '\x00\x00'.join(text).encode('utf-16-be', errors='ignore')
        elif encoding == 3:  # UTF-8
            data += '\x00'.join(text).encode('utf-8', errors='ignore')
        
        return data
    
    def _encode_comm_frame(self, frame):
        """Encode a comment frame."""
        encoding = getattr(frame, 'encoding', 3)
        lang = getattr(frame, 'lang', 'eng')
        desc = getattr(frame, 'desc', '')
        text = getattr(frame, 'text', '')
        
        data = bytes([encoding])
        data += lang[:3].encode('latin1', errors='ignore').ljust(3, b'\x00')
        
        if encoding == 0:  # Latin-1
            data += desc.encode('latin1', errors='ignore') + b'\x00'
            data += text.encode('latin1', errors='ignore')
        elif encoding == 1:  # UTF-16 with BOM
            data += desc.encode('utf-16') + b'\x00\x00'
            data += text.encode('utf-16')
        elif encoding == 2:  # UTF-16BE
            data += desc.encode('utf-16-be', errors='ignore') + b'\x00\x00'
            data += text.encode('utf-16-be', errors='ignore')
        elif encoding == 3:  # UTF-8
            data += desc.encode('utf-8', errors='ignore') + b'\x00'
            data += text.encode('utf-8', errors='ignore')
        
        return data
    
    def _encode_apic_frame(self, frame):
        """Encode a picture frame."""
        encoding = getattr(frame, 'encoding', 3)
        mime = getattr(frame, 'mime', 'image/jpeg')
        pic_type = getattr(frame, 'type', 3)
        desc = getattr(frame, 'desc', '')
        pic_data = getattr(frame, 'data', b'')
        
        data = bytes([encoding])
        data += mime.encode('latin1', errors='ignore') + b'\x00'
        data += bytes([pic_type])
        
        if encoding == 0:  # Latin-1
            data += desc.encode('latin1', errors='ignore') + b'\x00'
        elif encoding == 1:  # UTF-16 with BOM
            data += desc.encode('utf-16') + b'\x00\x00'
        elif encoding == 2:  # UTF-16BE
            data += desc.encode('utf-16-be', errors='ignore') + b'\x00\x00'
        elif encoding == 3:  # UTF-8
            data += desc.encode('utf-8', errors='ignore') + b'\x00'
        
        data += pic_data
        
        return data


class TextFrame:
    """Base class for text frames."""
    
    def __init__(self, encoding=3, text=None):
        self.encoding = encoding
        self.text = text if text is not None else []
        if isinstance(self.text, str):
            self.text = [self.text]


class TIT2(TextFrame):
    """Title/songname/content description."""
    pass


class TPE1(TextFrame):
    """Lead performer(s)/Soloist(s)."""
    pass


class TALB(TextFrame):
    """Album/Movie/Show title."""
    pass


class TDRC(TextFrame):
    """Recording time."""
    pass


class TRCK(TextFrame):
    """Track number/Position in set."""
    pass


class TCON(TextFrame):
    """Content type (genre)."""
    pass


class COMM:
    """Comment frame."""
    
    def __init__(self, encoding=3, lang='eng', desc='', text=''):
        self.encoding = encoding
        self.lang = lang
        self.desc = desc
        self.text = text


class APIC:
    """Attached picture frame."""
    
    def __init__(self, encoding=3, mime='image/jpeg', type=3, desc='', data=b''):
        self.encoding = encoding
        self.mime = mime
        self.type = type
        self.desc = desc
        self.data = data


def _get_text_frame_class(frame_id):
    """Get the text frame class for a given frame ID."""
    classes = {
        'TIT2': TIT2,
        'TPE1': TPE1,
        'TALB': TALB,
        'TDRC': TDRC,
        'TRCK': TRCK,
        'TCON': TCON,
    }
    return classes.get(frame_id, TextFrame)