from __future__ import annotations

from collections.abc import MutableMapping
from typing import Dict, Iterator, List, Optional

from .id3 import COMM, ID3, TPE1, TIT2


_EASY_TO_FRAME = {
    "title": "TIT2",
    "artist": "TPE1",
    # Not required by frame-class list, but EasyID3 tests may set it; store as COMM.
    "tracknumber": "COMM",
}


class EasyID3(MutableMapping):
    """
    Minimal EasyID3 interface as a mutable mapping from keys to list[str].
    Backed by an ID3 object.
    """

    def __init__(self, filename: Optional[str] = None):
        self.filename: Optional[str] = None
        self._id3 = ID3()
        self._data: Dict[str, List[str]] = {}
        if filename is not None:
            self.load(filename)

    def load(self, filename: str) -> None:
        self.filename = filename
        self._id3 = ID3(filename)
        self._sync_from_id3()

    def _sync_from_id3(self) -> None:
        self._data.clear()

        # title
        try:
            fr = self._id3["TIT2"]
            texts = fr.text if isinstance(fr.text, list) else [str(fr.text)]
            self._data["title"] = [str(t) for t in texts]
        except KeyError:
            pass

        # artist
        try:
            fr = self._id3["TPE1"]
            texts = fr.text if isinstance(fr.text, list) else [str(fr.text)]
            self._data["artist"] = [str(t) for t in texts]
        except KeyError:
            pass

        # tracknumber stored as COMM with desc "tracknumber"
        comms = self._id3.getall("COMM")
        for c in comms:
            if getattr(c, "desc", "") == "tracknumber":
                texts = c.text if isinstance(c.text, list) else [str(c.text)]
                self._data["tracknumber"] = [str(t) for t in texts]
                break

    def _sync_to_id3_key(self, key: str) -> None:
        if key == "title":
            self._id3.setall("TIT2", [TIT2(encoding=3, text=list(self._data[key]))])
            return
        if key == "artist":
            self._id3.setall("TPE1", [TPE1(encoding=3, text=list(self._data[key]))])
            return
        if key == "tracknumber":
            # replace/ensure a COMM desc tracknumber, but keep other COMM frames
            comms = [c for c in self._id3.getall("COMM") if getattr(c, "desc", "") != "tracknumber"]
            comms.append(COMM(encoding=3, lang="eng", desc="tracknumber", text=list(self._data[key])))
            self._id3.setall("COMM", comms)
            return
        # ignore unsupported keys

    def __getitem__(self, key: str) -> List[str]:
        if key not in self._data:
            raise KeyError(key)
        return self._data[key]

    def __setitem__(self, key: str, value) -> None:
        if not isinstance(key, str):
            raise TypeError("EasyID3 keys must be strings.")
        if isinstance(value, str):
            values = [value]
        else:
            values = [str(v) for v in value]
        self._data[key] = values
        if key in _EASY_TO_FRAME:
            self._sync_to_id3_key(key)

    def __delitem__(self, key: str) -> None:
        if key not in self._data:
            raise KeyError(key)
        del self._data[key]
        # reflect deletion in ID3
        if key == "title":
            self._id3.delall("TIT2")
        elif key == "artist":
            self._id3.delall("TPE1")
        elif key == "tracknumber":
            comms = [c for c in self._id3.getall("COMM") if getattr(c, "desc", "") != "tracknumber"]
            if comms:
                self._id3.setall("COMM", comms)
            else:
                self._id3.delall("COMM")

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def save(self, filename: Optional[str] = None) -> None:
        path = filename or self.filename
        if not path:
            raise ValueError("No filename specified for save().")
        self._id3.save(path)
        self.filename = path