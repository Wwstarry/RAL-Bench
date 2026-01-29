import struct
import io
from typing import Dict, List, Optional, Union, Any, BinaryIO

class ID3Error(Exception):
    """Base exception for ID3-related errors."""
    pass

class ID3:
    """Low-level ID3 tag interface."""
    
    def __init__(self, filename: Optional[str] = None):
        self._frames: Dict[str, List['Frame']] = {}
        self._filename: Optional[str] = None
        
        if filename:
            self.load(filename)
    
    def load(self, filename: str) -> None:
        """Load ID3 tags from file."""
        self._filename = filename
        self._frames.clear()
        
        try:
            with open(filename, 'rb') as f:
                # Check for ID3 header
                header = f.read(10)
                if len(header) < 10 or header[:3] != b'ID3':
                    return  # No ID3 tag
                
                # Parse header
                version_major, version_revision = header[3], header[4]
                flags = header[5]
                size = self._syncsafe_to_int(header[6:10])
                
                # Read tag data
                tag_data = f.read(size)
                
                # Parse frames
                pos = 0
                while pos < len(tag_data) - 10:
                    frame_id = tag_data[pos:pos+4].decode('ascii', errors='ignore')
                    if not frame_id.isalnum():
                        break
                    
                    frame_size = struct.unpack('>I', tag_data[pos+4:pos+8])[0]
                    frame_flags = struct.unpack('>H', tag_data[pos+8:pos+10])[0]
                    
                    frame_data = tag_data[pos+10:pos+10+frame_size]
                    pos += 10 + frame_size
                    
                    # Parse frame based on type
                    frame = self._parse_frame(frame_id, frame_data)
                    if frame:
                        self._frames.setdefault(frame_id, []).append(frame)
        except (IOError, struct.error):
            pass
    
    def _parse_frame(self, frame_id: str, data: bytes) -> Optional['Frame']:
        """Parse frame data into appropriate frame object."""
        if frame_id.startswith('T'):
            # Text frame
            encoding = data[0]
            text = data[1:].decode(self._get_encoding(encoding), errors='replace')
            if frame_id == 'TIT2':
                return TIT2(encoding=encoding, text=text)
            elif frame_id == 'TPE1':
                return TPE1(encoding=encoding, text=text)
        elif frame_id == 'COMM':
            # Comment frame
            encoding = data[0]
            lang = data[1:4].decode('ascii', errors='replace')
            desc_end = 4
            while desc_end < len(data) and data[desc_end] != 0:
                desc_end += 1
            desc = data[4:desc_end].decode(self._get_encoding(encoding), errors='replace')
            text = data[desc_end+1:].decode(self._get_encoding(encoding), errors='replace')
            return COMM(encoding=encoding, lang=lang, desc=desc, text=text)
        elif frame_id == 'APIC':
            # Picture frame
            encoding = data[0]
            mime_end = 1
            while mime_end < len(data) and data[mime_end] != 0:
                mime_end += 1
            mime = data[1:mime_end].decode('ascii', errors='replace')
            
            pic_type = data[mime_end+1]
            desc_start = mime_end + 2
            desc_end = desc_start
            while desc_end < len(data) and data[desc_end] != 0:
                desc_end += 1
            desc = data[desc_start:desc_end].decode(self._get_encoding(encoding), errors='replace')
            pic_data = data[desc_end+1:]
            return APIC(encoding=encoding, mime=mime, type=pic_type, desc=desc, data=pic_data)
        
        return None
    
    def _get_encoding(self, encoding_byte: int) -> str:
        """Get Python encoding name from ID3 encoding byte."""
        if encoding_byte == 0:
            return 'iso-8859-1'
        elif encoding_byte == 1:
            return 'utf-16'
        elif encoding_byte == 2:
            return 'utf-16be'
        elif encoding_byte == 3:
            return 'utf-8'
        return 'iso-8859-1'
    
    def _get_encoding_byte(self, encoding_str: str) -> int:
        """Get ID3 encoding byte from Python encoding name."""
        if encoding_str == 'iso-8859-1':
            return 0
        elif encoding_str == 'utf-16':
            return 1
        elif encoding_str == 'utf-16be':
            return 2
        elif encoding_str == 'utf-8':
            return 3
        return 0
    
    def _syncsafe_to_int(self, data: bytes) -> int:
        """Convert syncsafe integer to regular integer."""
        result = 0
        for byte in data:
            result = (result << 7) | (byte & 0x7F)
        return result
    
    def _int_to_syncsafe(self, value: int) -> bytes:
        """Convert integer to syncsafe bytes."""
        result = bytearray(4)
        for i in range(3, -1, -1):
            result[i] = value & 0x7F
            value >>= 7
        return bytes(result)
    
    def add(self, frame: 'Frame') -> None:
        """Add a frame to the tag."""
        frame_id = frame.frame_id
        self._frames.setdefault(frame_id, []).append(frame)
    
    def __getitem__(self, frame_id: str) -> 'Frame':
        """Get first frame with given ID."""
        if frame_id in self._frames and self._frames[frame_id]:
            return self._frames[frame_id][0]
        raise KeyError(frame_id)
    
    def getall(self, frame_id: str) -> List['Frame']:
        """Get all frames with given ID."""
        return self._frames.get(frame_id, [])
    
    def delall(self, frame_id: str) -> None:
        """Delete all frames with given ID."""
        if frame_id in self._frames:
            del self._frames[frame_id]
    
    def setall(self, frame_id: str, frames: List['Frame']) -> None:
        """Set all frames for given ID."""
        self._frames[frame_id] = frames.copy()
    
    def save(self, filename: Optional[str] = None) -> None:
        """Save ID3 tags to file."""
        save_filename = filename or self._filename
        if not save_filename:
            raise ValueError("No filename specified")
        
        # Prepare frames data
        frames_data = bytearray()
        for frame_id, frames in self._frames.items():
            for frame in frames:
                frame_bytes = frame._to_bytes()
                frame_size = len(frame_bytes)
                frames_data.extend(frame_id.encode('ascii'))
                frames_data.extend(struct.pack('>I', frame_size))
                frames_data.extend(b'\x00\x00')  # Flags
                frames_data.extend(frame_bytes)
        
        # Create ID3 header
        tag_size = len(frames_data)
        header = bytearray(b'ID3')
        header.append(3)  # Version 2.3.0
        header.append(0)
        header.append(0)  # Flags
        header.extend(self._int_to_syncsafe(tag_size))
        
        # Write to file
        with open(save_filename, 'wb') as f:
            f.write(header)
            f.write(frames_data)
        
        if not filename:
            self._filename = save_filename
    
    def __contains__(self, frame_id: str) -> bool:
        """Check if frame ID exists."""
        return frame_id in self._frames and bool(self._frames[frame_id])
    
    def __len__(self) -> int:
        """Number of frame types."""
        return len(self._frames)
    
    def __iter__(self):
        """Iterate over frame IDs."""
        return iter(self._frames)


class Frame:
    """Base class for ID3 frames."""
    
    def __init__(self, encoding: int = 0):
        self.encoding = encoding
    
    @property
    def frame_id(self) -> str:
        """Get frame ID."""
        return self.__class__.__name__
    
    def _to_bytes(self) -> bytes:
        """Convert frame to bytes."""
        raise NotImplementedError


class TextFrame(Frame):
    """Base class for text frames."""
    
    def __init__(self, encoding: int = 0, text: str = ""):
        super().__init__(encoding)
        self.text = text
    
    def _to_bytes(self) -> bytes:
        """Convert text frame to bytes."""
        encoding_name = ID3._get_encoding(self, self.encoding)
        encoded_text = self.text.encode(encoding_name)
        return bytes([self.encoding]) + encoded_text


class TIT2(TextFrame):
    """Title/songname/content description."""
    pass


class TPE1(TextFrame):
    """Lead performer(s)/soloist(s)."""
    pass


class COMM(Frame):
    """Comments frame."""
    
    def __init__(self, encoding: int = 0, lang: str = "eng", desc: str = "", text: str = ""):
        super().__init__(encoding)
        self.lang = lang
        self.desc = desc
        self.text = text
    
    def _to_bytes(self) -> bytes:
        """Convert comment frame to bytes."""
        encoding_name = ID3._get_encoding(self, self.encoding)
        lang_bytes = self.lang.encode('ascii')
        desc_bytes = self.desc.encode(encoding_name)
        text_bytes = self.text.encode(encoding_name)
        
        result = bytearray([self.encoding])
        result.extend(lang_bytes)
        result.extend(desc_bytes)
        result.append(0)  # Null separator
        result.extend(text_bytes)
        return bytes(result)


class APIC(Frame):
    """Attached picture frame."""
    
    def __init__(self, encoding: int = 0, mime: str = "", type: int = 0, desc: str = "", data: bytes = b""):
        super().__init__(encoding)
        self.mime = mime
        self.type = type
        self.desc = desc
        self.data = data
    
    def _to_bytes(self) -> bytes:
        """Convert picture frame to bytes."""
        encoding_name = ID3._get_encoding(self, self.encoding)
        mime_bytes = self.mime.encode('ascii')
        desc_bytes = self.desc.encode(encoding_name)
        
        result = bytearray([self.encoding])
        result.extend(mime_bytes)
        result.append(0)  # Null terminator for MIME
        result.append(self.type)
        result.extend(desc_bytes)
        result.append(0)  # Null separator
        result.extend(self.data)
        return bytes(result)