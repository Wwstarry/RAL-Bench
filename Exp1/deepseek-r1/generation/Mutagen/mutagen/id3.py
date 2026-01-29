import struct
from collections import defaultdict
from typing import Dict, List, Optional, Union, BinaryIO, Any

class ID3Error(Exception):
    """Base exception for ID3 errors."""
    pass

class ID3:
    """ID3 tag container."""
    
    def __init__(self, file: Optional[str] = None) -> None:
        self._frames: Dict[str, List[Any]] = defaultdict(list)
        self._filepath: Optional[str] = None
        
        if file:
            self.load(file)
    
    def load(self, file: str) -> None:
        """Load ID3 tag from file."""
        self._filepath = file
        self._frames.clear()
        
        try:
            with open(file, 'rb') as f:
                # Check for ID3 header
                header = f.read(10)
                if len(header) < 10 or not header.startswith(b'ID3'):
                    return
                
                # Parse tag size (sync-safe integer)
                tag_size = self._parse_syncsafe(header[6:10])
                
                # Read tag data
                tag_data = f.read(tag_size)
                pos = 0
                
                while pos < len(tag_data) - 10:
                    frame_id = tag_data[pos:pos+4].decode('ascii', errors='ignore')
                    if not frame_id.isalnum():
                        break
                    
                    frame_size = struct.unpack('>I', tag_data[pos+4:pos+8])[0]
                    flags = tag_data[pos+8:pos+10]
                    
                    if pos + 10 + frame_size > len(tag_data):
                        break
                    
                    frame_data = tag_data[pos+10:pos+10+frame_size]
                    pos += 10 + frame_size
                    
                    # Parse frame based on type
                    if frame_id.startswith('T'):
                        self._parse_text_frame(frame_id, frame_data)
                    elif frame_id == 'COMM':
                        self._parse_comm_frame(frame_data)
                    elif frame_id == 'APIC':
                        self._parse_apic_frame(frame_data)
        
        except (IOError, struct.error):
            pass
    
    def _parse_syncsafe(self, data: bytes) -> int:
        """Parse sync-safe integer."""
        return ((data[0] & 0x7F) << 21) | ((data[1] & 0x7F) << 14) | \
               ((data[2] & 0x7F) << 7) | (data[3] & 0x7F)
    
    def _encode_syncsafe(self, value: int) -> bytes:
        """Encode integer as sync-safe bytes."""
        return bytes([
            (value >> 21) & 0x7F,
            (value >> 14) & 0x7F,
            (value >> 7) & 0x7F,
            value & 0x7F
        ])
    
    def _parse_text_frame(self, frame_id: str, data: bytes) -> None:
        """Parse text frame."""
        if len(data) < 1:
            return
        
        encoding = data[0]
        if encoding == 0:  # ISO-8859-1
            text = data[1:].decode('latin-1', errors='replace')
        elif encoding == 1:  # UTF-16 with BOM
            text = data[3:].decode('utf-16', errors='replace')
        elif encoding == 2:  # UTF-16BE without BOM
            text = data[1:].decode('utf-16be', errors='replace')
        elif encoding == 3:  # UTF-8
            text = data[1:].decode('utf-8', errors='replace')
        else:
            return
        
        # Remove null terminators
        text = text.rstrip('\x00')
        
        if frame_id == 'TIT2':
            self._frames['TIT2'].append(TIT2(encoding, text))
        elif frame_id == 'TPE1':
            self._frames['TPE1'].append(TPE1(encoding, text))
    
    def _parse_comm_frame(self, data: bytes) -> None:
        """Parse comment frame."""
        if len(data) < 4:
            return
        
        encoding = data[0]
        lang = data[1:4].decode('ascii', errors='ignore')
        
        # Find description and text
        pos = 4
        desc_end = -1
        
        if encoding == 0:  # ISO-8859-1
            while pos < len(data) and data[pos] != 0:
                pos += 1
            desc = data[4:pos].decode('latin-1', errors='replace')
            pos += 1  # Skip null terminator
        elif encoding == 1:  # UTF-16 with BOM
            while pos + 1 < len(data) and (data[pos] != 0 or data[pos+1] != 0):
                pos += 2
            desc = data[4:pos].decode('utf-16', errors='replace')
            pos += 2  # Skip null terminator
        elif encoding == 3:  # UTF-8
            while pos < len(data) and data[pos] != 0:
                pos += 1
            desc = data[4:pos].decode('utf-8', errors='replace')
            pos += 1  # Skip null terminator
        else:
            return
        
        # Remaining data is text
        text_data = data[pos:]
        if encoding == 0:
            text = text_data.decode('latin-1', errors='replace')
        elif encoding == 1:
            text = text_data.decode('utf-16', errors='replace')
        elif encoding == 3:
            text = text_data.decode('utf-8', errors='replace')
        else:
            return
        
        self._frames['COMM'].append(COMM(encoding, lang, desc, text))
    
    def _parse_apic_frame(self, data: bytes) -> None:
        """Parse attached picture frame."""
        if len(data) < 1:
            return
        
        encoding = data[0]
        pos = 1
        
        # Parse MIME type
        if encoding == 0 or encoding == 3:  # ISO-8859-1 or UTF-8
            while pos < len(data) and data[pos] != 0:
                pos += 1
            mime = data[1:pos].decode('latin-1' if encoding == 0 else 'utf-8', errors='replace')
            pos += 1  # Skip null terminator
        elif encoding == 1:  # UTF-16 with BOM
            while pos + 1 < len(data) and (data[pos] != 0 or data[pos+1] != 0):
                pos += 2
            mime = data[1:pos].decode('utf-16', errors='replace')
            pos += 2  # Skip null terminator
        else:
            return
        
        if pos >= len(data):
            return
        
        # Picture type
        pic_type = data[pos]
        pos += 1
        
        # Parse description
        if encoding == 0 or encoding == 3:
            desc_start = pos
            while pos < len(data) and data[pos] != 0:
                pos += 1
            desc = data[desc_start:pos].decode('latin-1' if encoding == 0 else 'utf-8', errors='replace')
            pos += 1  # Skip null terminator
        elif encoding == 1:
            desc_start = pos
            while pos + 1 < len(data) and (data[pos] != 0 or data[pos+1] != 0):
                pos += 2
            desc = data[desc_start:pos].decode('utf-16', errors='replace')
            pos += 2  # Skip null terminator
        
        # Remaining data is picture data
        pic_data = data[pos:]
        
        self._frames['APIC'].append(APIC(encoding, mime, pic_type, desc, pic_data))
    
    def add(self, frame: Any) -> None:
        """Add a frame to the tag."""
        if hasattr(frame, '_frame_id'):
            self._frames[frame._frame_id].append(frame)
    
    def __getitem__(self, key: str) -> Any:
        """Get first frame with given ID."""
        if key in self._frames and self._frames[key]:
            return self._frames[key][0]
        raise KeyError(key)
    
    def getall(self, key: str) -> List[Any]:
        """Get all frames with given ID."""
        return self._frames.get(key, [])
    
    def delall(self, key: str) -> None:
        """Delete all frames with given ID."""
        if key in self._frames:
            del self._frames[key]
    
    def setall(self, key: str, frames: List[Any]) -> None:
        """Set frames for given ID."""
        self._frames[key] = frames.copy()
    
    def save(self, file: Optional[str] = None) -> None:
        """Save ID3 tag to file."""
        save_path = file or self._filepath
        if not save_path:
            raise ID3Error("No file specified")
        
        # Collect frame data
        frames_data = []
        total_size = 0
        
        for frame_id, frames in self._frames.items():
            for frame in frames:
                frame_data = frame._encode()
                frame_header = frame_id.encode('ascii') + struct.pack('>I', len(frame_data)) + b'\x00\x00'
                frames_data.append(frame_header + frame_data)
                total_size += len(frame_header) + len(frame_data)
        
        # Create ID3 header
        header = b'ID3' + b'\x03\x00' + self._encode_syncsafe(total_size)
        
        # Write to file
        with open(save_path, 'wb') as f:
            f.write(header)
            for frame in frames_data:
                f.write(frame)
        
        if not file:
            self._filepath = save_path
    
    def __contains__(self, key: str) -> bool:
        return key in self._frames and bool(self._frames[key])
    
    def __len__(self) -> int:
        return sum(len(frames) for frames in self._frames.values())


class _TextFrame:
    """Base class for text frames."""
    
    def __init__(self, encoding: int, text: str = ""):
        self.encoding = encoding
        self.text = text
    
    def _encode(self) -> bytes:
        """Encode frame data."""
        if self.encoding == 0:  # ISO-8859-1
            encoded_text = self.text.encode('latin-1')
        elif self.encoding == 1:  # UTF-16 with BOM
            encoded_text = b'\xff\xfe' + self.text.encode('utf-16le')
        elif self.encoding == 3:  # UTF-8
            encoded_text = self.text.encode('utf-8')
        else:
            encoded_text = self.text.encode('latin-1')
        
        return bytes([self.encoding]) + encoded_text


class TIT2(_TextFrame):
    """Title frame."""
    _frame_id = 'TIT2'


class TPE1(_TextFrame):
    """Artist frame."""
    _frame_id = 'TPE1'


class COMM:
    """Comment frame."""
    _frame_id = 'COMM'
    
    def __init__(self, encoding: int, lang: str, desc: str, text: str):
        self.encoding = encoding
        self.lang = lang
        self.desc = desc
        self.text = text
    
    def _encode(self) -> bytes:
        """Encode comment frame."""
        result = bytes([self.encoding])
        result += self.lang.encode('ascii')
        
        if self.encoding == 0:  # ISO-8859-1
            result += self.desc.encode('latin-1') + b'\x00'
            result += self.text.encode('latin-1')
        elif self.encoding == 1:  # UTF-16 with BOM
            result += b'\xff\xfe' + self.desc.encode('utf-16le') + b'\x00\x00'
            result += b'\xff\xfe' + self.text.encode('utf-16le')
        elif self.encoding == 3:  # UTF-8
            result += self.desc.encode('utf-8') + b'\x00'
            result += self.text.encode('utf-8')
        
        return result


class APIC:
    """Attached picture frame."""
    _frame_id = 'APIC'
    
    def __init__(self, encoding: int, mime: str, type: int, desc: str, data: bytes):
        self.encoding = encoding
        self.mime = mime
        self.type = type
        self.desc = desc
        self.data = data
    
    def _encode(self) -> bytes:
        """Encode picture frame."""
        result = bytes([self.encoding])
        
        if self.encoding == 0:  # ISO-8859-1
            result += self.mime.encode('latin-1') + b'\x00'
        elif self.encoding == 1:  # UTF-16 with BOM
            result += b'\xff\xfe' + self.mime.encode('utf-16le') + b'\x00\x00'
        elif self.encoding == 3:  # UTF-8
            result += self.mime.encode('utf-8') + b'\x00'
        
        result += bytes([self.type])
        
        if self.encoding == 0:
            result += self.desc.encode('latin-1') + b'\x00'
        elif self.encoding == 1:
            result += b'\xff\xfe' + self.desc.encode('utf-16le') + b'\x00\x00'
        elif self.encoding == 3:
            result += self.desc.encode('utf-8') + b'\x00'
        
        result += self.data
        return result