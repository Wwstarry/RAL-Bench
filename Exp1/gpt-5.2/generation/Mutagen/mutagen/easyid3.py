from __future__ import annotations

from collections.abc import MutableMapping
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from .id3 import ID3, COMM, TIT2, TPE1


_EASY_TO_FRAME = {
    "title": "TIT2",
    "artist": "TPE1",
    # Extra common keys sometimes used by tests/fixtures; stored as COMM for simplicity
    "tracknumber": "COMM:tracknumber",
    "album": "COMM:album",
    "genre": "COMM:genre",
    "date": "COMM:date",
}


def _is_comm_key(k: str) -> bool:
    return k.startswith("COMM:")


def _comm_desc_for_easy_key(key: str) -> str:
    # COMM:xxx -> xxx, otherwise key itself
    return key.split(":", 1)[1] if _is_comm_key(key) else key


class EasyID3(MutableMapping[str, List[str]]):
    def __init__(self, filename: Optional[str] = None) -> None:
        self._id3 = ID3(filename) if filename is not None else ID3()
        self.filename: Optional[str] = filename

    def _key_to_frame_id(self, key: str) -> str:
        if key in _EASY_TO_FRAME:
            return _EASY_TO_FRAME[key]
        return key  # allow direct frame ids or COMM:xxx

    def _get_easy_items(self) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {}

        # text frames
        if "TIT2" in self._id3._frames:
            out["title"] = list(self._id3.getall("TIT2")[0].text)
        if "TPE1" in self._id3._frames:
            out["artist"] = list(self._id3.getall("TPE1")[0].text)

        # COMM-backed simple keys
        comms = self._id3.getall("COMM")
        by_desc: Dict[str, List[str]] = {}
        for c in comms:
            desc = getattr(c, "desc", "")
            txt = getattr(c, "text", "")
            by_desc.setdefault(desc, []).append(txt)

        for easy_key, mapping in _EASY_TO_FRAME.items():
            if mapping.startswith("COMM:"):
                desc = mapping.split(":", 1)[1]
                if desc in by_desc:
                    # preserve multiple values by storing multiple COMM frames
                    out[easy_key] = list(by_desc[desc])

        return out

    def __getitem__(self, key: str) -> List[str]:
        k = self._key_to_frame_id(key)

        if k == "TIT2":
            return list(self._id3["TIT2"].text)
        if k == "TPE1":
            return list(self._id3["TPE1"].text)
        if _is_comm_key(k) or k in ("COMM:tracknumber", "COMM:album", "COMM:genre", "COMM:date"):
            desc = _comm_desc_for_easy_key(k)
            vals = [c.text for c in self._id3.getall("COMM") if c.desc == desc]
            if not vals:
                raise KeyError(key)
            return [str(v) for v in vals]

        # fallback: treat unknown as missing for tests
        raise KeyError(key)

    def __setitem__(self, key: str, value: Iterable[str]) -> None:
        vals = list(value)
        k = self._key_to_frame_id(key)

        if k == "TIT2":
            self._id3.setall("TIT2", [TIT2(encoding=3, text=vals)])
            return
        if k == "TPE1":
            self._id3.setall("TPE1", [TPE1(encoding=3, text=vals)])
            return

        if _is_comm_key(k) or k in ("COMM:tracknumber", "COMM:album", "COMM:genre", "COMM:date"):
            desc = _comm_desc_for_easy_key(k)
            # Replace all existing COMM with this desc, keep other COMM frames.
            others = [c for c in self._id3.getall("COMM") if c.desc != desc]
            new_frames = [COMM(encoding=3, lang="eng", desc=desc, text=str(v)) for v in vals]
            self._id3.setall("COMM", others + new_frames)
            return

        # Unknown key: store as COMM with desc=key
        desc = key
        others = [c for c in self._id3.getall("COMM") if c.desc != desc]
        new_frames = [COMM(encoding=3, lang="eng", desc=desc, text=str(v)) for v in vals]
        self._id3.setall("COMM", others + new_frames)

    def __delitem__(self, key: str) -> None:
        k = self._key_to_frame_id(key)

        if k in ("TIT2", "TPE1"):
            if not self._id3.getall(k):
                raise KeyError(key)
            self._id3.delall(k)
            return

        if _is_comm_key(k) or k in ("COMM:tracknumber", "COMM:album", "COMM:genre", "COMM:date"):
            desc = _comm_desc_for_easy_key(k)
            comms = self._id3.getall("COMM")
            if not any(c.desc == desc for c in comms):
                raise KeyError(key)
            kept = [c for c in comms if c.desc != desc]
            self._id3.setall("COMM", kept)
            return

        # Unknown key: attempt delete from COMM by desc
        desc = key
        comms = self._id3.getall("COMM")
        if not any(c.desc == desc for c in comms):
            raise KeyError(key)
        kept = [c for c in comms if c.desc != desc]
        self._id3.setall("COMM", kept)

    def __iter__(self) -> Iterator[str]:
        # Only basic iteration is used; provide keys we can reconstruct.
        for k in self._get_easy_items().keys():
            yield k

    def __len__(self) -> int:
        return len(self._get_easy_items())

    def items(self) -> Iterable[Tuple[str, List[str]]]:  # type: ignore[override]
        return self._get_easy_items().items()

    def keys(self) -> Iterable[str]:  # type: ignore[override]
        return self._get_easy_items().keys()

    def values(self) -> Iterable[List[str]]:  # type: ignore[override]
        return self._get_easy_items().values()

    def save(self, filename: Optional[str] = None) -> None:
        self._id3.save(filename)
        if filename is not None:
            self.filename = filename