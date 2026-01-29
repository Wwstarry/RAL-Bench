from collections.abc import MutableMapping
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TCON, TDRC

class EasyID3(MutableMapping):
    # Mapping from EasyID3 keys to ID3 Frame classes
    _KEY_MAP = {
        "title": TIT2,
        "artist": TPE1,
        "album": TALB,
        "tracknumber": TRCK,
        "genre": TCON,
        "date": TDRC,
    }

    # Reverse mapping for iteration if needed, though we iterate keys based on content
    _FRAME_MAP = {v.__name__: k for k, v in _KEY_MAP.items()}

    def __init__(self, path=None):
        self.filename = path
        if path:
            self.id3 = ID3(path)
        else:
            self.id3 = ID3()

    def __getitem__(self, key):
        frame_class = self._KEY_MAP.get(key)
        if not frame_class:
            raise KeyError(key)
        
        frame_id = frame_class.__name__
        frames = self.id3.getall(frame_id)
        
        if not frames:
            raise KeyError(key)
        
        # EasyID3 returns a list of strings. 
        # In ID3v2, text frames usually contain a list of strings.
        # We aggregate all text from all frames of this type.
        values = []
        for f in frames:
            if hasattr(f, 'text'):
                values.extend(f.text)
        return values

    def __setitem__(self, key, value):
        frame_class = self._KEY_MAP.get(key)
        if not frame_class:
            raise KeyError(f"Unknown EasyID3 key: {key}")
        
        if not isinstance(value, list):
            value = [value]
            
        frame_id = frame_class.__name__
        
        # Create a new frame with the given text
        # Note: Standard Mutagen EasyID3 often replaces the whole set of frames for a key
        new_frame = frame_class(encoding=3, text=value)
        self.id3.setall(frame_id, [new_frame])

    def __delitem__(self, key):
        frame_class = self._KEY_MAP.get(key)
        if not frame_class:
            raise KeyError(key)
        
        frame_id = frame_class.__name__
        if not self.id3.getall(frame_id):
            raise KeyError(key)
            
        self.id3.delall(frame_id)

    def __iter__(self):
        # Yield keys that exist in the underlying ID3 tag
        for frame_id in self.id3._frames:
            if frame_id in self._FRAME_MAP:
                yield self._FRAME_MAP[frame_id]

    def __len__(self):
        count = 0
        for frame_id in self.id3._frames:
            if frame_id in self._FRAME_MAP:
                count += 1
        return count

    def save(self, path=None):
        self.id3.save(path)