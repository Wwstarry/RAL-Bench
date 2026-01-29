import os
import struct

class ID3:
    """ID3 tag container."""
    
    def __init__(self, filename=None):
        self._frames = {}
        if filename is not None:
            self.load(filename)
    
    def load(self, filename):
        """Load ID3 tags from file."""
        try:
            with open(filename, 'rb') as f:
                header = f.read(10)
                if header[:3] != b'ID3':
                    return
                
                size = self._parse_size(header[6:10])
                tag_data = f.read(size)
                self._parse_frames(tag_data)
        except (IOError, OSError):
            pass
    
    def _parse_size(self, size_bytes):
        return (size_bytes[0] << 21) | (size_bytes[1] << 14) | \
               (size_bytes[2] << 7) | size_bytes[3]
    
    def _parse_frames(self, data):
        pos = 0
        while pos + 10 <= len(data):
            frame_id = data[pos:pos+4].decode('ascii', errors='ignore')
            if not frame_id.isalnum():
                break
                
            frame_size = struct.unpack('>I', data[pos+4:pos+8])[0]
            flags = data[pos+8:pos+10]
            frame_data = data[pos+10:pos+10+frame_size]
            
            if frame_id in {'TIT2', 'TPE1'}:
                encoding = frame_data[0]
                text = frame_data[1:].decode('utf-8' if encoding == 3 else 'latin-1')
                frame = globals()[frame_id](encoding=encoding, text=text)
                self.add(frame)
            elif frame_id == 'COMM':
                encoding = frame_data[0]
                lang = frame_data[1:4].decode('ascii')
                desc_end = frame_data[4:].find(b'\x00') + 4
                desc = frame_data[4:desc_end].decode('utf-8' if encoding == 3 else 'latin-1')
                text = frame_data[desc_end+1:].decode('utf-8' if encoding == 3 else 'latin-1')
                frame = COMM(encoding=encoding, lang=lang, desc=desc, text=text)
                self.add(frame)
            elif frame_id == 'APIC':
                encoding = frame_data[0]
                mime_end = frame_data[1:].find(b'\x00') + 1
                mime = frame_data[1:mime_end].decode('latin-1')
                frame_type = frame_data[mime_end+0]
                desc_end = frame_data[mime_end+1:].find(b'\x00') + mime_end + 1
                desc = frame_data[mime_end+1:desc_end].decode('utf-8' if encoding == 3 else 'latin-1')
                data = frame_data[desc_end+1:]
                frame = APIC(encoding=encoding, mime=mime, type=frame_type, desc=desc, data=data)
                self.add(frame)
            
            pos += 10 + frame_size
    
    def add(self, frame):
        """Add a frame to the tag."""
        if frame.FrameID not in self._frames:
            self._frames[frame.FrameID] = []
        self._frames[frame.FrameID].append(frame)
    
    def __getitem__(self, frame_id):
        """Get the first frame with the given ID."""
        return self._frames[frame_id][0]
    
    def getall(self, frame_id):
        """Get all frames with the given ID."""
        return self._frames.get(frame_id, [])
    
    def delall(self, frame_id):
        """Delete all frames with the given ID."""
        if frame_id in self._frames:
            del self._frames[frame_id]
    
    def setall(self, frame_id, frames):
        """Set all frames for the given ID."""
        self._frames[frame_id] = list(frames)
    
    def save(self, filename):
        """Save ID3 tags to file."""
        with open(filename, 'wb') as f:
            # Write ID3 header (version 2.3)
            f.write(b'ID3\x03\x00\x00')
            
            # Collect frame data
            frame_data = b''
            for frame_id, frames in self._frames.items():
                for frame in frames:
                    frame_bytes = frame._write()
                    frame_data += frame_id.encode('ascii')
                    frame_data += struct.pack('>I', len(frame_bytes))
                    frame_data += b'\x00\x00'  # flags
                    frame_data += frame_bytes
            
            # Write size (sync-safe)
            size = len(frame_data)
            f.write(bytes([
                (size >> 21) & 0x7F,
                (size >> 14) & 0x7F,
                (size >> 7) & 0x7F,
                size & 0x7F
            ]))
            
            # Write frames
            f.write(frame_data)

class Frame:
    """Base ID3 frame class."""
    FrameID = None
    
    def _write(self):
        raise NotImplementedError

class TextFrame(Frame):
    """Text frame base class."""
    
    def __init__(self, encoding, text):
        self.encoding = encoding
        self.text = text
    
    def _write(self):
        return bytes([self.encoding]) + self.text.encode('utf-8' if self.encoding == 3 else 'latin-1')

class TIT2(TextFrame):
    """Title/songname/content description."""
    FrameID = 'TIT2'

class TPE1(TextFrame):
    """Lead performer(s)/Soloist(s)."""
    FrameID = 'TPE1'

class COMM(Frame):
    """Comments frame."""
    FrameID = 'COMM'
    
    def __init__(self, encoding, lang, desc, text):
        self.encoding = encoding
        self.lang = lang
        self.desc = desc
        self.text = text
    
    def _write(self):
        data = bytes([self.encoding])
        data += self.lang.encode('ascii')
        data += self.desc.encode('utf-8' if self.encoding == 3 else 'latin-1')
        data += b'\x00'
        data += self.text.encode('utf-8' if self.encoding == 3 else 'latin-1')
        return data

class APIC(Frame):
    """Attached picture frame."""
    FrameID = 'APIC'
    
    def __init__(self, encoding, mime, type, desc, data):
        self.encoding = encoding
        self.mime = mime
        self.type = type
        self.desc = desc
        self.data = data
    
    def _write(self):
        data = bytes([self.encoding])
        data += self.mime.encode('latin-1')
        data += b'\x00'
        data += bytes([self.type])
        data += self.desc.encode('utf-8' if self.encoding == 3 else 'latin-1')
        data += b'\x00'
        data += self.data
        return data