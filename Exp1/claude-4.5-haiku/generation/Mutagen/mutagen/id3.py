"""
Low-level ID3 tag implementation.

This module provides the ID3 class for reading and writing ID3v2.4 tags,
along with frame classes for different types of ID3 frames.
"""

import struct
import io
from typing import List, Dict, Optional, Any


def _synchsafe_encode(value: int) -> bytes:
    """Encode an integer as a synchsafe integer (7 bits per byte)."""
    return bytes([
        (value >> 21) & 0x7f,
        (value >> 14) & 0x7f,
        (value >> 7) & 0x7f,
        value & 0x7f,
    ])


def _synchsafe_decode(data: bytes) -> int:
    """Decode a synchsafe integer (7 bits per byte)."""
    if len(data) < 4:
        return 0
    return (
        ((data[0] & 0x7f) << 21) |
        ((data[1] & 0x7f) << 14) |
        ((data[2] & 0x7f) << 7) |
        (data[3] & 0x7f)
    )


class Frame:
    """Base class for ID3 frames."""
    
    frame_id = None
    
    def __init__(self, encoding=3, **kwargs):
        self.encoding = encoding
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def _encode_text(self, text: str, encoding: int) -> bytes:
        """Encode text with the given encoding."""
        if encoding == 0:
            return text.encode('latin-1') + b'\x00'
        elif encoding == 1:
            return b'\xff\xfe' + text.encode('utf-16-le') + b'\x00\x00'
        elif encoding == 2:
            return text.encode('utf-16-be') + b'\x00\x00'
        elif encoding == 3:
            return text.encode('utf-8') + b'\x00'
        else:
            return text.encode('utf-8') + b'\x00'
    
    def _decode_text(self, data: bytes, encoding: int) -> str:
        """Decode text with the given encoding."""
        if encoding == 0:
            return data.rstrip(b'\x00').decode('latin-1')
        elif encoding == 1:
            if data.startswith(b'\xff\xfe'):
                return data[2:].rstrip(b'\x00\x00').decode('utf-16-le')
            else:
                return data.rstrip(b'\x00\x00').decode('utf-16-le')
        elif encoding == 2:
            return data.rstrip(b'\x00\x00').decode('utf-16-be')
        elif encoding == 3:
            return data.rstrip(b'\x00').decode('utf-8')
        else:
            return data.rstrip(b'\x00').decode('utf-8')
    
    def _render(self) -> bytes:
        """Render the frame to bytes. Override in subclasses."""
        return b''
    
    @staticmethod
    def _parse(frame_id: str, data: bytes) -> 'Frame':
        """Parse frame data. Override in subclasses."""
        return Frame()


class TextFrame(Frame):
    """Base class for text frames."""
    
    def __init__(self, encoding=3, text=None, **kwargs):
        super().__init__(encoding=encoding, **kwargs)
        self.text = text if text is not None else []
        if isinstance(self.text, str):
            self.text = [self.text]
    
    def _render(self) -> bytes:
        """Render text frame to bytes."""
        data = bytes([self.encoding])
        text_str = '\x00'.join(self.text) if isinstance(self.text, list) else self.text
        data += self._encode_text(text_str, self.encoding)
        return data
    
    @staticmethod
    def _parse_text(data: bytes) -> tuple:
        """Parse text frame data."""
        if len(data) < 1:
            return 0, []
        encoding = data[0]
        text_data = data[1:]
        
        if encoding == 0:
            text = text_data.rstrip(b'\x00').decode('latin-1')
        elif encoding == 1:
            if text_data.startswith(b'\xff\xfe'):
                text = text_data[2:].rstrip(b'\x00\x00').decode('utf-16-le')
            else:
                text = text_data.rstrip(b'\x00\x00').decode('utf-16-le')
        elif encoding == 2:
            text = text_data.rstrip(b'\x00\x00').decode('utf-16-be')
        elif encoding == 3:
            text = text_data.rstrip(b'\x00').decode('utf-8')
        else:
            text = text_data.rstrip(b'\x00').decode('utf-8')
        
        text_list = text.split('\x00') if text else []
        return encoding, text_list


class TIT2(TextFrame):
    """Title frame."""
    frame_id = "TIT2"


class TPE1(TextFrame):
    """Lead performer/artist frame."""
    frame_id = "TPE1"


class COMM(Frame):
    """Comment frame."""
    frame_id = "COMM"
    
    def __init__(self, encoding=3, lang="eng", desc="", text=None, **kwargs):
        super().__init__(encoding=encoding, **kwargs)
        self.lang = lang
        self.desc = desc
        self.text = text if text is not None else []
        if isinstance(self.text, str):
            self.text = [self.text]
    
    def _render(self) -> bytes:
        """Render comment frame to bytes."""
        data = bytes([self.encoding])
        data += self.lang.encode('latin-1')[:3].ljust(3, b'\x00')
        data += self._encode_text(self.desc, self.encoding)
        text_str = '\x00'.join(self.text) if isinstance(self.text, list) else self.text
        data += self._encode_text(text_str, self.encoding)
        return data
    
    @staticmethod
    def _parse(data: bytes) -> 'COMM':
        """Parse comment frame."""
        if len(data) < 4:
            return COMM()
        encoding = data[0]
        lang = data[1:4].decode('latin-1', errors='ignore')
        
        # Find description and text
        rest = data[4:]
        if encoding == 0:
            parts = rest.split(b'\x00', 1)
            desc = parts[0].decode('latin-1', errors='ignore')
            text_data = parts[1] if len(parts) > 1 else b''
            text = text_data.rstrip(b'\x00').decode('latin-1', errors='ignore')
        elif encoding == 1:
            if rest.startswith(b'\xff\xfe'):
                parts = rest.split(b'\x00\x00', 1)
                desc = (b'\xff\xfe' + parts[0][2:]).rstrip(b'\x00\x00').decode('utf-16-le', errors='ignore')
                text_data = parts[1] if len(parts) > 1 else b''
                text = text_data.rstrip(b'\x00\x00').decode('utf-16-le', errors='ignore')
            else:
                parts = rest.split(b'\x00\x00', 1)
                desc = parts[0].rstrip(b'\x00\x00').decode('utf-16-le', errors='ignore')
                text_data = parts[1] if len(parts) > 1 else b''
                text = text_data.rstrip(b'\x00\x00').decode('utf-16-le', errors='ignore')
        elif encoding == 3:
            parts = rest.split(b'\x00', 1)
            desc = parts[0].decode('utf-8', errors='ignore')
            text_data = parts[1] if len(parts) > 1 else b''
            text = text_data.rstrip(b'\x00').decode('utf-8', errors='ignore')
        else:
            desc = ""
            text = ""
        
        return COMM(encoding=encoding, lang=lang, desc=desc, text=[text] if text else [])


class APIC(Frame):
    """Attached picture frame."""
    frame_id = "APIC"
    
    def __init__(self, encoding=3, mime="image/jpeg", type=0, desc="", data=None, **kwargs):
        super().__init__(encoding=encoding, **kwargs)
        self.mime = mime
        self.type = type
        self.desc = desc
        self.data = data if data is not None else b''
    
    def _render(self) -> bytes:
        """Render picture frame to bytes."""
        frame_data = bytes([self.encoding])
        frame_data += self.mime.encode('latin-1') + b'\x00'
        frame_data += bytes([self.type])
        frame_data += self._encode_text(self.desc, self.encoding)
        frame_data += self.data
        return frame_data
    
    @staticmethod
    def _parse(data: bytes) -> 'APIC':
        """Parse picture frame."""
        if len(data) < 2:
            return APIC()
        encoding = data[0]
        rest = data[1:]
        
        # Find MIME type
        mime_end = rest.find(b'\x00')
        if mime_end == -1:
            return APIC()
        mime = rest[:mime_end].decode('latin-1', errors='ignore')
        rest = rest[mime_end + 1:]
        
        if len(rest) < 1:
            return APIC(encoding=encoding, mime=mime)
        
        pic_type = rest[0]
        rest = rest[1:]
        
        # Find description
        if encoding == 0:
            desc_end = rest.find(b'\x00')
            desc = rest[:desc_end].decode('latin-1', errors='ignore') if desc_end != -1 else ""
            pic_data = rest[desc_end + 1:] if desc_end != -1 else rest
        elif encoding == 1:
            desc_end = rest.find(b'\x00\x00')
            if desc_end != -1:
                desc = rest[:desc_end].decode('utf-16-le', errors='ignore')
                pic_data = rest[desc_end + 2:]
            else:
                desc = rest.rstrip(b'\x00\x00').decode('utf-16-le', errors='ignore')
                pic_data = b''
        elif encoding == 3:
            desc_end = rest.find(b'\x00')
            desc = rest[:desc_end].decode('utf-8', errors='ignore') if desc_end != -1 else ""
            pic_data = rest[desc_end + 1:] if desc_end != -1 else rest
        else:
            desc = ""
            pic_data = rest
        
        return APIC(encoding=encoding, mime=mime, type=pic_type, desc=desc, data=pic_data)


class ID3:
    """ID3v2.4 tag container."""
    
    def __init__(self, path: Optional[str] = None):
        """Initialize ID3 tag, optionally from a file."""
        self.frames: Dict[str, List[Frame]] = {}
        self._path = path
        if path:
            self._load(path)
    
    def _load(self, path: str) -> None:
        """Load ID3 tag from file."""
        try:
            with open(path, 'rb') as f:
                data = f.read()
        except (IOError, OSError):
            return
        
        if len(data) < 10 or data[:3] != b'ID3':
            return
        
        version = data[3:5]
        flags = data[5]
        size = _synchsafe_decode(data[6:10])
        
        if size > len(data) - 10:
            size = len(data) - 10
        
        tag_data = data[10:10 + size]
        self._parse_frames(tag_data)
    
    def _parse_frames(self, data: bytes) -> None:
        """Parse frames from tag data."""
        pos = 0
        while pos < len(data) - 10:
            frame_id = data[pos:pos + 4].decode('latin-1', errors='ignore').rstrip('\x00')
            if not frame_id or frame_id[0] == '\x00':
                break
            
            size_bytes = data[pos + 4:pos + 8]
            size = _synchsafe_decode(size_bytes)
            flags = data[pos + 8:pos + 10]
            
            frame_data = data[pos + 10:pos + 10 + size]
            pos += 10 + size
            
            frame = self._create_frame(frame_id, frame_data)
            if frame:
                if frame_id not in self.frames:
                    self.frames[frame_id] = []
                self.frames[frame_id].append(frame)
    
    def _create_frame(self, frame_id: str, data: bytes) -> Optional[Frame]:
        """Create a frame object from frame ID and data."""
        if frame_id == "TIT2":
            encoding, text = TextFrame._parse_text(data)
            return TIT2(encoding=encoding, text=text)
        elif frame_id == "TPE1":
            encoding, text = TextFrame._parse_text(data)
            return TPE1(encoding=encoding, text=text)
        elif frame_id == "COMM":
            return COMM._parse(data)
        elif frame_id == "APIC":
            return APIC._parse(data)
        else:
            return None
    
    def add(self, frame: Frame) -> None:
        """Add a frame to the tag."""
        frame_id = frame.frame_id
        if frame_id not in self.frames:
            self.frames[frame_id] = []
        self.frames[frame_id].append(frame)
    
    def __getitem__(self, frame_id: str) -> Frame:
        """Get the first frame with the given ID."""
        if frame_id not in self.frames or not self.frames[frame_id]:
            raise KeyError(frame_id)
        return self.frames[frame_id][0]
    
    def getall(self, frame_id: str) -> List[Frame]:
        """Get all frames with the given ID."""
        return self.frames.get(frame_id, [])
    
    def delall(self, frame_id: str) -> None:
        """Delete all frames with the given ID."""
        if frame_id in self.frames:
            del self.frames[frame_id]
    
    def setall(self, frame_id: str, frames: List[Frame]) -> None:
        """Set all frames for the given ID."""
        self.frames[frame_id] = frames
    
    def _render(self) -> bytes:
        """Render the tag to bytes."""
        frame_data = b''
        
        for frame_id in sorted(self.frames.keys()):
            for frame in self.frames[frame_id]:
                frame_bytes = frame._render()
                size = len(frame_bytes)
                size_bytes = _synchsafe_encode(size)
                frame_header = frame_id.encode('latin-1').ljust(4, b'\x00')
                frame_header += size_bytes
                frame_header += b'\x00\x00'
                frame_data += frame_header + frame_bytes
        
        tag_size = len(frame_data)
        size_bytes = _synchsafe_encode(tag_size)
        header = b'ID3\x04\x00\x00' + size_bytes
        
        return header + frame_data
    
    def save(self, path: Optional[str] = None) -> None:
        """Save the tag to a file."""
        if path is None:
            path = self._path
        if path is None:
            raise ValueError("No path specified")
        
        tag_data = self._render()
        
        try:
            with open(path, 'r+b') as f:
                existing = f.read()
        except (IOError, OSError):
            existing = b''
        
        # Check if there's an existing ID3 tag
        if existing.startswith(b'ID3'):
            # Find the end of the existing tag
            if len(existing) >= 10:
                size = _synchsafe_decode(existing[6:10])
                audio_start = 10 + size
                audio_data = existing[audio_start:]
            else:
                audio_data = b''
        else:
            audio_data = existing
        
        # Write new tag + audio data
        with open(path, 'wb') as f:
            f.write(tag_data)
            f.write(audio_data)
        
        self._path = path