from typing import Dict, List, Optional, Iterable
from collections.abc import MutableMapping

from .id3 import ID3, TIT2, TPE1, TRCK


# Mapping between EasyID3 keys and ID3 frame classes
_EASY_MAP = {
    "title": ("TIT2", TIT2),
    "artist": ("TPE1", TPE1),
    "tracknumber": ("TRCK", TRCK),
}


class EasyID3(MutableMapping):
    def __init__(self, path: Optional[str] = None):
        self._id3 = ID3(path) if path else ID3()
        self._path = path
        self._data: Dict[str, List[str]] = {}
        if path:
            self._load_from_id3()

    def _load_from_id3(self):
        # Load mapped keys from ID3 frames into our dict
        for key, (fid, cls) in _EASY_MAP.items():
            values: List[str] = []
            frames = self._id3.getall(fid)
            if not frames:
                continue
            # For TextFrame, combine all values from all frames
            for frame in frames:
                if hasattr(frame, "text"):
                    # frame.text is a list of strings
                    values.extend([str(t) for t in frame.text])
            if values:
                self._data[key] = values

    def save(self, path: Optional[str] = None):
        # Apply current mapping to underlying ID3 object
        # For each mapped key present, write a single frame with multiple values
        for key, (fid, cls) in _EASY_MAP.items():
            if key in self._data:
                values = self._data.get(key, [])
                # Create single frame with possibly multiple values
                frame = cls(encoding=3, text=values)
                self._id3.setall(fid, [frame])
            else:
                # Remove any frames for keys not present
                self._id3.delall(fid)
        # Save underlying ID3
        target = path if path is not None else self._path
        self._id3.save(target)
        if path is not None:
            self._path = path

    # MutableMapping interface
    def __getitem__(self, key: str) -> List[str]:
        if key not in _EASY_MAP:
            raise KeyError(key)
        if key not in self._data:
            raise KeyError(key)
        return self._data[key]

    def __setitem__(self, key: str, value: Iterable[str]):
        if key not in _EASY_MAP:
            raise KeyError(key)
        # Ensure value is a list of strings
        if isinstance(value, (str, bytes)):
            if isinstance(value, bytes):
                try:
                    value = value.decode("utf-8")
                except Exception:
                    value = value.decode("latin1", "replace")
            self._data[key] = [str(value)]
        else:
            self._data[key] = [str(v) for v in value]

    def __delitem__(self, key: str):
        if key not in _EASY_MAP:
            raise KeyError(key)
        if key not in self._data:
            raise KeyError(key)
        del self._data[key]
        # Also remove from underlying frames immediately for in-memory state consistency
        fid, _ = _EASY_MAP[key]
        self._id3.delall(fid)

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()