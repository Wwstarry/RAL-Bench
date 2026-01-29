from __future__ import annotations

from collections.abc import MutableMapping, Iterator
from typing import Dict, List, Optional, Tuple, Any

from .id3 import ID3, TIT2, TPE1, TRCK


_EASY_TO_FRAME = {
    "title": "TIT2",
    "artist": "TPE1",
    "tracknumber": "TRCK",
}

_FRAME_TO_EASY = {v: k for k, v in _EASY_TO_FRAME.items()}


class EasyID3(MutableMapping[str, List[str]]):
    """
    Minimal EasyID3 implementation compatible with core behaviors used in tests.
    Acts like a mapping of easy keys -> list[str], persisted via our ID3 container.
    """

    def __init__(self, filename: Optional[str] = None):
        self.filename: Optional[str] = None
        self._data: Dict[str, List[str]] = {}
        if filename is not None:
            self.load(filename)

    def load(self, filename: str) -> None:
        id3 = ID3(filename)
        self.filename = filename
        data: Dict[str, List[str]] = {}
        # Pull mapped frames
        for fid, easy in _FRAME_TO_EASY.items():
            try:
                fr = id3[fid]
            except KeyError:
                continue
            txt = getattr(fr, "text", None)
            if isinstance(txt, list):
                data[easy] = [str(x) for x in txt]
            elif txt is None:
                continue
            else:
                data[easy] = [str(txt)]
        self._data = data

    def __getitem__(self, key: str) -> List[str]:
        if key not in self._data:
            raise KeyError(key)
        return self._data[key]

    def __setitem__(self, key: str, value: List[str]) -> None:
        if not isinstance(key, str):
            raise TypeError("EasyID3 keys must be str")
        if isinstance(value, (str, bytes)):
            raise TypeError("EasyID3 values must be list[str]")
        if not isinstance(value, list):
            raise TypeError("EasyID3 values must be list[str]")
        self._data[key] = [str(x) for x in value]

    def __delitem__(self, key: str) -> None:
        if key not in self._data:
            raise KeyError(key)
        del self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def _to_id3(self, base: Optional[ID3] = None) -> ID3:
        id3 = base if base is not None else ID3()
        # Update mapped frames; ensure deletions propagate by removing mapped frames
        for easy_key, fid in _EASY_TO_FRAME.items():
            if easy_key in self._data:
                vals = self._data[easy_key]
                if fid == "TIT2":
                    id3.setall("TIT2", [TIT2(3, text=vals)])
                elif fid == "TPE1":
                    id3.setall("TPE1", [TPE1(3, text=vals)])
                elif fid == "TRCK":
                    id3.setall("TRCK", [TRCK(3, text=vals)])
            else:
                id3.delall(fid)
        return id3

    def save(self, path: Optional[str] = None) -> None:
        out_path = path or self.filename
        if not out_path:
            raise ValueError("No filename specified for save()")

        # If saving to existing file, load it to preserve non-easy frames (COMM/APIC)
        base: Optional[ID3] = None
        if path is None:
            # We were loaded from a file; preserve all other frames.
            base = ID3(self.filename) if self.filename else ID3()
        else:
            try:
                base = ID3(out_path)
            except FileNotFoundError:
                base = ID3()

        id3 = self._to_id3(base)
        id3.save(out_path)
        self.filename = out_path