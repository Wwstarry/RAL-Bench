import os
from mutagen.id3 import ID3, TextFrame, TIT2, TPE1, TRCK, TALB


EASY_MAPPING = {
    "title": "TIT2",
    "artist": "TPE1",
    "tracknumber": "TRCK",
    "album": "TALB",
    # Add more mappings as needed
}

class EasyID3:
    """
    A high-level interface to ID3 tags, focusing on text keys like title, artist, etc.
    Behaves like a dict from string -> list of strings.
    """

    def __init__(self, filething=None):
        """
        If filething is given, load tags from that file.
        Otherwise, create an empty tagging context.
        """
        self._path = filething if isinstance(filething, str) else None
        self._tags = {}  # key -> list of strings
        self._loaded = bool(self._path)
        self._id3 = None

        if self._path and os.path.isfile(self._path):
            # read existing ID3
            self._id3 = ID3(self._path)
            self._read_from_id3()
        else:
            self._id3 = ID3()  # empty

    def _read_from_id3(self):
        """
        Parse the ID3 object, extracting known text frames into self._tags.
        """
        # Clear existing
        self._tags = {}

        # Go through frames in self._id3, see if they map to known easy keys
        for frame_id, frames in self._id3.frames.items():
            if not frames:
                continue
            # We'll just look at the first one if it's a text frame
            # or combine them if needed. But typically for easy keys, we store them in one frame.
            primary_frame = frames[0]
            # Check if known text frame:
            if hasattr(primary_frame, 'text'):
                # see which easy key this might correspond to
                easy_key = None
                for k, v in EASY_MAPPING.items():
                    if v == frame_id:
                        easy_key = k
                        break
                if easy_key:
                    # Combine text from the first frame.
                    # If we'd want multiple frames, we'd handle differently, but usually we do a single.
                    # For multiple artists, we store them in text list.
                    self._tags[easy_key] = list(primary_frame.text)

    def _write_to_id3(self):
        """
        Update self._id3 frames from self._tags dictionary.
        This overwrites any mapped frames with new content.
        """
        # For each mapped key, set or remove the corresponding ID3 frame
        for easy_key, frame_id in EASY_MAPPING.items():
            if easy_key in self._tags:
                text_list = self._tags[easy_key]
                # Overwrite the ID3 frame
                frame_cls = {
                    "TIT2": TIT2,
                    "TPE1": TPE1,
                    "TRCK": TRCK,
                    "TALB": TALB
                }.get(frame_id, TextFrame)

                frm = frame_cls(encoding=3, text=text_list)
                self._id3.setall(frame_id, [frm])
            else:
                self._id3.delall(frame_id)

    def __getitem__(self, key):
        if key not in self._tags:
            raise KeyError(key)
        return self._tags[key]

    def __setitem__(self, key, value):
        # value must be a list of strings
        if not isinstance(value, list):
            raise TypeError("Value must be a list of strings")
        self._tags[key] = value

    def __delitem__(self, key):
        if key not in self._tags:
            raise KeyError(key)
        del self._tags[key]

    def __iter__(self):
        return iter(self._tags)

    def keys(self):
        return self._tags.keys()

    def items(self):
        return self._tags.items()

    def values(self):
        return self._tags.values()

    def save(self, path=None):
        """
        Writes changes to disk. If path is given, writes to that path (creating a tag-only
        file if necessary). If no path is given, overwrites the original file this was
        loaded from (if any).
        """
        outpath = path or self._path
        # build ID3 frames from self._tags
        self._write_to_id3()
        self._id3.save(path=outpath)