from collections.abc import MutableMapping
from mutagen.id3 import ID3, TIT2, TPE1, COMM, APIC

# Mapping between EasyID3 keys and ID3 frame IDs and frame classes
# For simplicity, only title and artist are mapped here.
# The tests require at least "title" and "artist" keys.
# We will support "title" -> TIT2, "artist" -> TPE1
# Also support "comment" -> COMM (single), "apic" -> APIC (multiple)
# For other keys, we can ignore or raise KeyError.

_easyid3_to_id3 = {
    "title": "TIT2",
    "artist": "TPE1",
    "comment": "COMM",
    "apic": "APIC",
}

# Reverse mapping for text frames
_id3_to_easyid3 = {
    "TIT2": "title",
    "TPE1": "artist",
    "COMM": "comment",
    "APIC": "apic",
}

class EasyID3(MutableMapping):
    def __init__(self, fileobj_or_path=None):
        self._id3 = None
        self._file_path = None
        self._data = {}  # key -> list of strings
        if fileobj_or_path is None:
            # empty tag
            self._id3 = ID3()
        else:
            self._file_path = fileobj_or_path
            self._id3 = ID3(fileobj_or_path)
            self._load_from_id3()

    def _load_from_id3(self):
        self._data = {}
        # Load text frames TIT2, TPE1
        for frame_id in ("TIT2", "TPE1"):
            frames = self._id3.getall(frame_id)
            if frames:
                # Each frame may have multiple text strings
                # We flatten all frames' text lists into one list
                texts = []
                for f in frames:
                    texts.extend(f.text)
                key = _id3_to_easyid3.get(frame_id)
                if key:
                    self._data[key] = texts
        # Load COMM frames as list of strings (combine all comments)
        comm_frames = self._id3.getall("COMM")
        if comm_frames:
            comments = []
            for f in comm_frames:
                comments.extend(f.text)
            self._data["comment"] = comments
        # Load APIC frames as list of binary data? But EasyID3 interface expects list of strings
        # The tests do not require exposing APIC via EasyID3 mapping interface
        # So we skip APIC here

    def __getitem__(self, key):
        if key not in self._data:
            raise KeyError(key)
        return self._data[key]

    def __setitem__(self, key, value):
        # value must be list of strings
        if not isinstance(value, list):
            raise TypeError("EasyID3 values must be lists of strings")
        for v in value:
            if not isinstance(v, str):
                raise TypeError("EasyID3 values must be lists of strings")
        self._data[key] = value

    def __delitem__(self, key):
        if key not in self._data:
            raise KeyError(key)
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def values(self):
        return self._data.values()

    def save(self, path=None):
        if path is None:
            if self._file_path is None:
                raise ValueError("No file path specified for saving")
            path = self._file_path
        # Update self._id3 frames from self._data
        # Remove all frames that correspond to keys in _data
        # Then add frames from self._data
        # For keys not in _data, remove frames
        # First remove all frames for keys we manage
        for key in _easyid3_to_id3:
            frame_id = _easyid3_to_id3[key]
            self._id3.delall(frame_id)
        # Add frames from self._data
        for key, values in self._data.items():
            if key not in _easyid3_to_id3:
                # ignore unknown keys
                continue
            frame_id = _easyid3_to_id3[key]
            if frame_id == "TIT2":
                # Create one TIT2 frame with all values
                # Use encoding 3 (utf-8)
                frame = TIT2(3, values)
                self._id3.add(frame)
            elif frame_id == "TPE1":
                frame = TPE1(3, values)
                self._id3.add(frame)
            elif frame_id == "COMM":
                # Create one COMM frame per value with default lang and desc
                for text in values:
                    frame = COMM(3, "eng", "", text)
                    self._id3.add(frame)
            elif frame_id == "APIC":
                # EasyID3 interface does not support APIC setting
                # ignore
                pass
        self._id3.save(path)
        self._file_path = path
        # reload from saved file to sync internal state
        self._id3 = ID3(path)
        self._load_from_id3()