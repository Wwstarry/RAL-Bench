from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, Dict, Iterator, List, Optional

from .id3 import ID3, TIT2, TPE1


def _norm_list(v: Any) -> List[str]:
    if isinstance(v, (list, tuple)):
        return [str(x) for x in v]
    return [str(v)]


_KEY_TO_FID = {
    "title": "TIT2",
    "artist": "TPE1",
}


class EasyID3(MutableMapping):
    def __init__(self, filename: Optional[str] = None):
        self._id3 = ID3(filename) if filename is not None else ID3()

    def __getitem__(self, key: str) -> List[str]:
        fid = _KEY_TO_FID.get(key)
        if fid is None:
            raise KeyError(key)
        fr = self._id3[fid]
        # Frames store .text as list[str]
        return list(getattr(fr, "text", []))

    def __setitem__(self, key: str, value: Any) -> None:
        fid = _KEY_TO_FID.get(key)
        if fid is None:
            raise KeyError(key)
        vals = _norm_list(value)
        if fid == "TIT2":
            self._id3.setall(fid, [TIT2(3, text=vals)])
        elif fid == "TPE1":
            self._id3.setall(fid, [TPE1(3, text=vals)])
        else:
            raise KeyError(key)

    def __delitem__(self, key: str) -> None:
        fid = _KEY_TO_FID.get(key)
        if fid is None:
            raise KeyError(key)
        # Raise KeyError if missing
        if not self._id3.getall(fid):
            raise KeyError(key)
        self._id3.delall(fid)

    def __iter__(self) -> Iterator[str]:
        for k, fid in _KEY_TO_FID.items():
            if self._id3.getall(fid):
                yield k

    def __len__(self) -> int:
        return sum(1 for _ in self.__iter__())

    def save(self, filename: Optional[str] = None) -> None:
        self._id3.save(filename)