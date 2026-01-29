"""
EasyID3 - High-level ID3 tag interface.
"""

from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, TCON


# Mapping from EasyID3 keys to ID3 frame IDs
_EASY_MAP = {
    "title": "TIT2",
    "artist": "TPE1",
    "album": "TALB",
    "date": "TDRC",
    "tracknumber": "TRCK",
    "genre": "TCON",
}


class EasyID3:
    """
    High-level ID3 tag interface that behaves like a dict mapping
    string keys to lists of strings.
    """
    
    def __init__(self, filename=None):
        """
        Create an EasyID3 instance.
        
        Args:
            filename: Optional path to an MP3 file to load tags from.
        """
        self._filename = filename
        self._id3 = ID3(filename) if filename else ID3()
    
    def __getitem__(self, key):
        """
        Get tag values for a key.
        
        Args:
            key: Tag key (e.g., "title", "artist")
            
        Returns:
            List of string values
            
        Raises:
            KeyError: If the key is not present
        """
        if key not in _EASY_MAP:
            raise KeyError(key)
        
        frame_id = _EASY_MAP[key]
        frames = self._id3.getall(frame_id)
        
        if not frames:
            raise KeyError(key)
        
        # Collect all text values from all frames
        values = []
        for frame in frames:
            if hasattr(frame, 'text'):
                values.extend(frame.text)
        
        return values
    
    def __setitem__(self, key, value):
        """
        Set tag values for a key.
        
        Args:
            key: Tag key (e.g., "title", "artist")
            value: List of string values
        """
        if key not in _EASY_MAP:
            raise KeyError(key)
        
        frame_id = _EASY_MAP[key]
        
        # Remove existing frames
        self._id3.delall(frame_id)
        
        # Add new frame with the values
        if value:
            frame_class = _get_frame_class(frame_id)
            frame = frame_class(encoding=3, text=value)
            self._id3.add(frame)
    
    def __delitem__(self, key):
        """
        Delete a tag key.
        
        Args:
            key: Tag key to delete
            
        Raises:
            KeyError: If the key is not present
        """
        if key not in _EASY_MAP:
            raise KeyError(key)
        
        frame_id = _EASY_MAP[key]
        frames = self._id3.getall(frame_id)
        
        if not frames:
            raise KeyError(key)
        
        self._id3.delall(frame_id)
    
    def __contains__(self, key):
        """Check if a key is present."""
        if key not in _EASY_MAP:
            return False
        
        frame_id = _EASY_MAP[key]
        frames = self._id3.getall(frame_id)
        return len(frames) > 0
    
    def keys(self):
        """Return an iterator over tag keys."""
        for key in _EASY_MAP:
            if key in self:
                yield key
    
    def values(self):
        """Return an iterator over tag values."""
        for key in self.keys():
            yield self[key]
    
    def items(self):
        """Return an iterator over (key, value) pairs."""
        for key in self.keys():
            yield key, self[key]
    
    def __iter__(self):
        """Iterate over keys."""
        return self.keys()
    
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
        
        self._id3.save(filename)


def _get_frame_class(frame_id):
    """Get the frame class for a given frame ID."""
    frame_classes = {
        "TIT2": TIT2,
        "TPE1": TPE1,
        "TALB": TALB,
        "TDRC": TDRC,
        "TRCK": TRCK,
        "TCON": TCON,
    }
    return frame_classes.get(frame_id, TIT2)