"""
High-level ID3 tag interface.

This module provides the EasyID3 class for easy reading and writing of ID3 tags
using a simple dictionary-like interface with string keys and list values.
"""

from typing import Optional, List, Dict, Any
from mutagen.id3 import ID3, TIT2, TPE1, COMM, APIC


# Mapping from easy tag names to ID3 frame IDs
EASY_TO_ID3 = {
    'title': 'TIT2',
    'artist': 'TPE1',
    'album': 'TALB',
    'date': 'TDRC',
    'genre': 'TCON',
    'tracknumber': 'TRCK',
    'albumartist': 'TPE2',
    'composer': 'TCOM',
    'comment': 'COMM',
}

ID3_TO_EASY = {v: k for k, v in EASY_TO_ID3.items()}


class EasyID3:
    """High-level ID3 tag interface."""
    
    def __init__(self, path: Optional[str] = None):
        """Initialize EasyID3 tag, optionally from a file."""
        self._id3 = ID3(path)
        self._path = path
        self._tags: Dict[str, List[str]] = {}
        self._load_easy_tags()
    
    def _load_easy_tags(self) -> None:
        """Load tags from ID3 into easy tag format."""
        self._tags = {}
        
        for frame_id, frames in self._id3.frames.items():
            easy_name = ID3_TO_EASY.get(frame_id)
            if easy_name:
                values = []
                for frame in frames:
                    if hasattr(frame, 'text'):
                        if isinstance(frame.text, list):
                            values.extend(frame.text)
                        else:
                            values.append(frame.text)
                if values:
                    self._tags[easy_name] = values
            elif frame_id == 'COMM':
                # Handle comments specially
                values = []
                for frame in frames:
                    if hasattr(frame, 'text'):
                        if isinstance(frame.text, list):
                            values.extend(frame.text)
                        else:
                            values.append(frame.text)
                if values:
                    self._tags['comment'] = values
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set a tag value."""
        if isinstance(value, str):
            value = [value]
        elif not isinstance(value, list):
            value = list(value)
        
        self._tags[key] = value
    
    def __getitem__(self, key: str) -> List[str]:
        """Get a tag value."""
        if key not in self._tags:
            raise KeyError(key)
        return self._tags[key]
    
    def __delitem__(self, key: str) -> None:
        """Delete a tag."""
        if key not in self._tags:
            raise KeyError(key)
        del self._tags[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if a tag exists."""
        return key in self._tags
    
    def __iter__(self):
        """Iterate over tag keys."""
        return iter(self._tags)
    
    def keys(self):
        """Get tag keys."""
        return self._tags.keys()
    
    def values(self):
        """Get tag values."""
        return self._tags.values()
    
    def items(self):
        """Get tag items."""
        return self._tags.items()
    
    def get(self, key: str, default=None):
        """Get a tag value with a default."""
        return self._tags.get(key, default)
    
    def _sync_to_id3(self) -> None:
        """Synchronize easy tags back to ID3 frames."""
        # Clear existing frames
        self._id3.frames.clear()
        
        for easy_name, values in self._tags.items():
            frame_id = EASY_TO_ID3.get(easy_name)
            
            if not frame_id:
                continue
            
            if easy_name == 'comment':
                # Handle comments
                frame = COMM(encoding=3, lang='eng', desc='', text=values)
                self._id3.frames['COMM'] = [frame]
            elif frame_id == 'TIT2':
                frame = TIT2(encoding=3, text=values)
                self._id3.frames['TIT2'] = [frame]
            elif frame_id == 'TPE1':
                frame = TPE1(encoding=3, text=values)
                self._id3.frames['TPE1'] = [frame]
            else:
                # Generic text frame
                frame = TIT2(encoding=3, text=values)
                frame.frame_id = frame_id
                self._id3.frames[frame_id] = [frame]
    
    def save(self, path: Optional[str] = None) -> None:
        """Save tags to a file."""
        if path is None:
            path = self._path
        if path is None:
            raise ValueError("No path specified")
        
        self._sync_to_id3()
        self._id3.save(path)
        self._path = path