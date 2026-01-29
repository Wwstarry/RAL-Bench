"""
A *very* slim “EasyID3” wrapper around our in-house `mutagen.id3.ID3` shim.

It exposes a Mapping-like interface with *user friendly* keys (e.g. "title"
instead of "TIT2") and stores string lists in the underlying ID3 text frames.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Iterator, List, MutableMapping, Optional

from . import id3 as _id3_mod

# --------------------------------------------------------------------------- #
#  Key ↔ frame mapping helpers
# --------------------------------------------------------------------------- #
# Map from human key  -> (frame_class, frame_id)
_KEYMAP: Dict[str, tuple[type[_id3_mod.Frame], str]] = {
    "title": (_id3_mod.TIT2, _id3_mod.TIT2.FrameID),
    "artist": (_id3_mod.TPE1, _id3_mod.TPE1.FrameID),
    "album": (_id3_mod.TALB, _id3_mod.TALB.FrameID),
    "tracknumber": (_id3_mod.TRCK, _id3_mod.TRCK.FrameID),
    "discnumber": (_id3_mod.TPOS, _id3_mod.TPOS.FrameID),
    "date": (_id3_mod.TDRC, _id3_mod.TDRC.FrameID),
}


def _get_frame_cls_for_key(key: str) -> type[_id3_mod.Frame]:
    if key not in _KEYMAP:
        raise KeyError(f"unsupported EasyID3 key: {key!r}")
    return _KEYMAP[key][0]


def _get_frame_id_for_key(key: str) -> str:
    if key not in _KEYMAP:
        raise KeyError(f"unsupported EasyID3 key: {key!r}")
    return _KEYMAP[key][1]


# --------------------------------------------------------------------------- #
#  The main EasyID3 implementation
# --------------------------------------------------------------------------- #
class EasyID3(MutableMapping[str, List[str]]):
    """
    Simplified *EasyID3* wrapper.

    Only supports the operations needed by the challenge test-suite:
        * construction from file / empty
        * dict-like item access (`__getitem__`, `__setitem__`, `__delitem__`)
        * `.save([path])`
    """

    def __init__(self, filename: str | Path | None = None) -> None:
        self.filename: Optional[Path] = None
        if filename is None:
            self._id3 = _id3_mod.ID3()
        else:
            self.filename = Path(filename)
            self._id3 = _id3_mod.ID3(self.filename)

    # ------------------------------------------------------------------ #
    # Mapping interface
    # ------------------------------------------------------------------ #
    def __getitem__(self, key: str) -> List[str]:
        frame_id = _get_frame_id_for_key(key)
        try:
            frame = self._id3[frame_id]
        except KeyError:
            raise KeyError(key) from None

        # Text frames store list[str] in `.text`
        if hasattr(frame, "text"):
            return list(frame.text)  # copy
        raise KeyError(key)

    def __setitem__(self, key: str, values: Iterable[str]) -> None:
        # ensure list[str]
        val_list: List[str] = [str(v) for v in values]
        frame_cls = _get_frame_cls_for_key(key)
        frame_id = _get_frame_id_for_key(key)

        # Create one new frame that holds *all* values in its `.text`
        new_frame = frame_cls(encoding=3, text=val_list)

        # Replace old frames
        self._id3.setall(frame_id, [new_frame])

    def __delitem__(self, key: str) -> None:
        frame_id = _get_frame_id_for_key(key)
        try:
            self._id3.delall(frame_id)
        except Exception:
            # make sure correct error type is bubbled
            raise KeyError(key) from None

    def __iter__(self) -> Iterator[str]:
        # Only iterate over *present* easy keys
        for k in _KEYMAP:
            frame_id = _get_frame_id_for_key(k)
            if frame_id in self._id3:
                yield k

    def __len__(self) -> int:
        return sum(1 for _ in self)

    # Provide the usual helpers
    def keys(self):
        return list(iter(self))

    def items(self):
        return [(k, self[k]) for k in self]

    def values(self):
        return [self[k] for k in self]

    # ------------------------------------------------------------------ #
    # Convenience pass-through for lower-level access
    # ------------------------------------------------------------------ #
    def add(self, frame: _id3_mod.Frame) -> None:
        """Add a low-level frame directly (Rarely used by tests)."""
        self._id3.add(frame)

    # ------------------------------------------------------------------ #
    # Saving
    # ------------------------------------------------------------------ #
    def save(self, filename: str | Path | None = None) -> None:
        """Write tags back to disk.

        Behaviour:
            * `filename is None` – overwrite the original file the tag was
              loaded from (must exist).
            * otherwise – write to given path (creates/overwrites).  The EasyID3
              instance is now associated with that new file.
        """
        target: Optional[Path]
        if filename is None:
            if self.filename is None:
                raise ValueError("No filename associated with tag and none supplied.")
            target = self.filename
        else:
            target = Path(filename)
            # update our internal reference
            self.filename = target

        self._id3.save(target)

    # ------------------------------------------------------------------ #
    # String representation (nice for debugging)
    # ------------------------------------------------------------------ #
    def __repr__(self) -> str:  # pragma: no cover
        kv = ", ".join(f"{k}={v!r}" for k, v in self.items())
        return f"<EasyID3 {kv}>"