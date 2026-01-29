from collections.abc import MutableMapping
from .id3 import ID3, TIT2, TPE1, TALB, TRCK, TDRC, TCON

class EasyID3(MutableMapping):
    """
    A high-level, dictionary-like interface for ID3 tags.
    """
    _EASY_MAP = {
        'title': 'TIT2',
        'artist': 'TPE1',
        'album': 'TALB',
        'tracknumber': 'TRCK',
        'date': 'TDRC',
        'genre': 'TCON',
    }
    
    _FRAME_CLASSES = {
        'TIT2': TIT2, 'TPE1': TPE1, 'TALB': TALB, 'TRCK': TRCK,
        'TDRC': TDRC, 'TCON': TCON,
    }

    def __init__(self, filename=None):
        self.id3 = ID3(filename)
        self._REVERSE_MAP = {v: k for k, v in self._EASY_MAP.items()}

    def __getitem__(self, key):
        key = key.lower()
        if key not in self._EASY_MAP:
            raise KeyError(key)
        
        frame_id = self._EASY_MAP[key]
        frames = self.id3.getall(frame_id)
        
        if not frames:
            raise KeyError(key)
            
        return [frame.text for frame in frames]

    def __setitem__(self, key, value):
        key = key.lower()
        if key not in self._EASY_MAP:
            raise KeyError(f"EasyID3 key '{key}' not recognized")

        frame_id = self._EASY_MAP[key]
        self.id3.delall(frame_id)
        
        if not isinstance(value, list):
            value = [value]
        
        frame_class = self._FRAME_CLASSES.get(frame_id)
        if frame_class:
            for v in value:
                frame = frame_class(encoding=3, text=str(v))
                self.id3.add(frame)

    def __delitem__(self, key):
        key = key.lower()
        if key not in self._EASY_MAP:
            raise KeyError(key)
        
        frame_id = self._EASY_MAP[key]
        if not self.id3.getall(frame_id):
            raise KeyError(key)
        
        self.id3.delall(frame_id)

    def __iter__(self):
        present_keys = set()
        for frame_id in self.id3.frames.keys():
            if frame_id in self._REVERSE_MAP:
                present_keys.add(self._REVERSE_MAP[frame_id])
        return iter(sorted(list(present_keys)))

    def __len__(self):
        count = 0
        for frame_id in self.id3.frames.keys():
            if frame_id in self._REVERSE_MAP:
                count += 1
        return count

    def save(self, filename=None):
        """Save the tags to a file."""
        self.id3.save(filename)