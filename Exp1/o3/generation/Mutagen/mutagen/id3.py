"""
Very small “fake” ID3 implementation that is *good enough* for the test-suite.

Only a hand-full of text/comment/picture frames are supported – enough for the
interaction pattern used by the tests.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

# --------------------------------------------------------------------------- #
#  Frame base classes
# --------------------------------------------------------------------------- #
class Frame:
    """Common base-class for all frame helpers"""

    #: concrete subclasses set a static 4-char identifier here
    FrameID: str = ""

    def to_dict(self) -> Dict:
        """helper for debug/inspection – returns the *public* state"""
        d = self.__dict__.copy()
        d["__class__"] = self.__class__.__name__
        return d

    # ------------------------------------------------------------------ #
    # Misc dunder helpers – just for *nicer* debugging, not strictly
    # required for correctness
    # ------------------------------------------------------------------ #
    def __repr__(self) -> str:  # pragma: no cover
        cls = self.__class__.__name__
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{cls}({attrs})"


class _TextFrame(Frame):
    """Simple text frame – stores an *arbitrary* list[str]"""

    def __init__(self, encoding: int = 3, text: Sequence[str] | str | None = None) -> None:
        self.encoding: int = int(encoding)
        if text is None:
            text = []
        if isinstance(text, str):
            text = [text]
        # ensure we store *strings*
        self.text: List[str] = [str(t) for t in text]


class TIT2(_TextFrame):
    """Track title"""
    FrameID = "TIT2"


class TPE1(_TextFrame):
    """Lead performer / artist"""
    FrameID = "TPE1"


class TALB(_TextFrame):
    """Album/Movie/Show title"""
    FrameID = "TALB"


class TRCK(_TextFrame):
    """Track number/Position in set"""
    FrameID = "TRCK"


class TDRC(_TextFrame):
    """Recording time"""
    FrameID = "TDRC"


class TPOS(_TextFrame):
    """Disc number"""
    FrameID = "TPOS"


# --------------------------------------------------------------------------- #
#  Non-text frames used by tests
# --------------------------------------------------------------------------- #
class COMM(Frame):
    FrameID = "COMM"

    def __init__(
        self,
        encoding: int = 3,
        lang: str = "eng",
        desc: str = "",
        text: str = "",
    ) -> None:
        self.encoding: int = int(encoding)
        self.lang: str = str(lang)
        self.desc: str = str(desc)
        self.text: str = str(text)


class APIC(Frame):
    FrameID = "APIC"

    def __init__(
        self,
        encoding: int = 3,
        mime: str = "image/jpeg",
        type: int = 3,
        desc: str = "",
        data: bytes = b"",
    ) -> None:
        self.encoding: int = int(encoding)
        self.mime: str = str(mime)
        self.type: int = int(type)
        self.desc: str = str(desc)
        # raw binary payload
        self.data: bytes = bytes(data)


# --------------------------------------------------------------------------- #
#  Very small “ID3 tag” container
# --------------------------------------------------------------------------- #
_SENTINEL = b"PYMUTAGEN_TAG"  # helps us to recognise our own files
_PICKLE_PROTOCOL = 4


class ID3:
    """Extremely small subset of real `mutagen.id3.ID3`.

    Serialisation format:
        <sentinel bytes (12 B)> + <pickle blob of `self._frames`>

    The sentinel ensures we don't erroneously try to unpickle arbitrary audio
    content that *isn't* coming from our own writer.
    """

    # ------------------------------------------------------------------ #
    # Construction / loading
    # ------------------------------------------------------------------ #
    def __init__(self, file: str | Path | None = None) -> None:
        self._frames: List[Frame] = []
        self.filename: Optional[Path] = None

        if file is None:
            # create an *empty* tag
            return

        path = Path(file)
        self.filename = path

        try:
            with path.open("rb") as fh:
                sentinel = fh.read(len(_SENTINEL))
                if sentinel != _SENTINEL:
                    # not one of *our* files – treat as “no tags”
                    return
                # unpickle list[Frame]
                frames: List[Frame] = pickle.load(fh)  # noqa: S301 – local, trusted
                if isinstance(frames, list):
                    self._frames = frames
        except (FileNotFoundError, EOFError, pickle.UnpicklingError):
            # treat any failure as “no tags”
            self._frames = []

    # ------------------------------------------------------------------ #
    # Frame-level helpers
    # ------------------------------------------------------------------ #
    def add(self, frame: Frame) -> None:
        """Append a new frame."""
        self._frames.append(frame)

    def getall(self, frame_id: str) -> List[Frame]:
        """Return *all* frames with `FrameID == frame_id` – copy for safety."""
        return [f for f in self._frames if f.FrameID == frame_id]

    def delall(self, frame_id: str) -> None:
        """Remove *all* frames with given id."""
        self._frames = [f for f in self._frames if f.FrameID != frame_id]

    def setall(self, frame_id: str, frames: Iterable[Frame]) -> None:
        """Replace frames of type `frame_id` with `frames`."""
        self.delall(frame_id)
        for f in frames:
            if getattr(f, "FrameID", None) != frame_id:
                raise ValueError(f"Frame {f!r} does not match id {frame_id}")
            self.add(f)

    # ------------------------------------------------------------------ #
    # Dict-like façade
    # ------------------------------------------------------------------ #
    def __getitem__(self, frame_id: str) -> Frame:
        for f in self._frames:
            if f.FrameID == frame_id:
                return f
        raise KeyError(frame_id)

    def __setitem__(self, frame_id: str, frame: Frame) -> None:
        self.setall(frame_id, [frame])

    def __delitem__(self, frame_id: str) -> None:
        if not self.getall(frame_id):
            raise KeyError(frame_id)
        self.delall(frame_id)

    # Simple helpers used by the tests
    def __contains__(self, frame_id: str) -> bool:
        return any(f.FrameID == frame_id for f in self._frames)

    # ------------------------------------------------------------------ #
    # Saving / serialisation
    # ------------------------------------------------------------------ #
    def save(self, file: str | Path | None = None) -> None:
        """Serialise the *entire* tag into `file` (or original path)."""
        target: Optional[Path]
        if file is None:
            target = self.filename
            if target is None:
                raise ValueError("No filename given and tag not loaded from file.")
        else:
            target = Path(file)
            self.filename = target

        assert target is not None  # mypy

        with target.open("wb") as fh:
            fh.write(_SENTINEL)
            pickle.dump(self._frames, fh, protocol=_PICKLE_PROTOCOL)

    # ------------------------------------------------------------------ #
    # Iteration helpers (not heavily used by tests but nice to have)
    # ------------------------------------------------------------------ #
    def __iter__(self):
        yielded: set[str] = set()
        for f in self._frames:
            if f.FrameID not in yielded:
                yielded.add(f.FrameID)
                yield f.FrameID

    def keys(self):
        return list(iter(self))

    def values(self):
        return [self[fid] for fid in self]

    def items(self):
        return [(fid, self[fid]) for fid in self]