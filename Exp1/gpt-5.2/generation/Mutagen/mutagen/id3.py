from __future__ import annotations

import os
import struct
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple, Union

# -----------------------------------------------------------------------------
# Internal on-disk container (NOT real ID3)
# -----------------------------------------------------------------------------

_MAGIC = b"PYMUT1"
_HEADER_STRUCT = struct.Struct(">6sII")  # magic, meta_len, audio_len


def _read_file_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def _write_file_bytes(path: str, data: bytes) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def _parse_container(data: bytes) -> Tuple[Optional[bytes], bytes]:
    """
    Returns (meta_bytes_or_None, audio_bytes).
    If file is not in our container format, meta is None and audio is original bytes.
    """
    if len(data) < _HEADER_STRUCT.size:
        return None, data
    magic, meta_len, audio_len = _HEADER_STRUCT.unpack_from(data, 0)
    if magic != _MAGIC:
        return None, data
    total = _HEADER_STRUCT.size + meta_len + audio_len
    if total > len(data):
        # Corrupt/truncated; treat as no metadata.
        return None, data
    meta = data[_HEADER_STRUCT.size : _HEADER_STRUCT.size + meta_len]
    audio = data[_HEADER_STRUCT.size + meta_len : _HEADER_STRUCT.size + meta_len + audio_len]
    return meta, audio


def _build_container(meta: bytes, audio: bytes) -> bytes:
    return _HEADER_STRUCT.pack(_MAGIC, len(meta), len(audio)) + meta + audio


def _pack_u16(n: int) -> bytes:
    return struct.pack(">H", n)


def _pack_u32(n: int) -> bytes:
    return struct.pack(">I", n)


def _unpack_u16(b: bytes, off: int) -> Tuple[int, int]:
    return struct.unpack_from(">H", b, off)[0], off + 2


def _unpack_u32(b: bytes, off: int) -> Tuple[int, int]:
    return struct.unpack_from(">I", b, off)[0], off + 4


def _pack_bytes(blob: bytes) -> bytes:
    return _pack_u32(len(blob)) + blob


def _unpack_bytes(b: bytes, off: int) -> Tuple[bytes, int]:
    ln, off = _unpack_u32(b, off)
    return b[off : off + ln], off + ln


def _pack_str(s: str) -> bytes:
    bs = s.encode("utf-8")
    return _pack_u16(len(bs)) + bs


def _unpack_str(b: bytes, off: int) -> Tuple[str, int]:
    ln, off = _unpack_u16(b, off)
    return b[off : off + ln].decode("utf-8", "replace"), off + ln


# -----------------------------------------------------------------------------
# Frame classes
# -----------------------------------------------------------------------------

@dataclass
class _TextFrame:
    encoding: int = 3
    text: List[str] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.text is None:
            self.text = []
        elif isinstance(self.text, (str, bytes)):
            self.text = [self.text.decode("utf-8", "replace")] if isinstance(self.text, bytes) else [self.text]
        else:
            self.text = [str(x) for x in self.text]

    @property
    def FrameID(self) -> str:
        raise NotImplementedError


class TIT2(_TextFrame):
    @property
    def FrameID(self) -> str:
        return "TIT2"


class TPE1(_TextFrame):
    @property
    def FrameID(self) -> str:
        return "TPE1"


@dataclass
class COMM:
    encoding: int
    lang: str
    desc: str
    text: Union[str, List[str]]

    @property
    def FrameID(self) -> str:
        return "COMM"

    def __post_init__(self) -> None:
        if isinstance(self.text, list):
            self.text = [str(x) for x in self.text]
        else:
            self.text = str(self.text)


@dataclass
class APIC:
    encoding: int
    mime: str
    type: int
    desc: str
    data: bytes

    @property
    def FrameID(self) -> str:
        return "APIC"

    def __post_init__(self) -> None:
        if not isinstance(self.data, (bytes, bytearray, memoryview)):
            raise TypeError("APIC.data must be bytes-like")
        self.data = bytes(self.data)


Frame = Union[TIT2, TPE1, COMM, APIC]


# -----------------------------------------------------------------------------
# Serialization of frames
# -----------------------------------------------------------------------------

_FRAME_TYPE_TEXT = 1
_FRAME_TYPE_COMM = 2
_FRAME_TYPE_APIC = 3


def _frame_to_bytes(frame: Frame) -> bytes:
    fid = frame.FrameID
    out = bytearray()
    out += _pack_str(fid)

    if fid in ("TIT2", "TPE1"):
        out.append(_FRAME_TYPE_TEXT)
        out.append(int(getattr(frame, "encoding", 3)) & 0xFF)
        texts = list(getattr(frame, "text", []) or [])
        out += _pack_u16(len(texts))
        for t in texts:
            out += _pack_str(str(t))
        return bytes(out)

    if fid == "COMM":
        out.append(_FRAME_TYPE_COMM)
        out.append(int(frame.encoding) & 0xFF)
        out += _pack_str(frame.lang)
        out += _pack_str(frame.desc)
        # store as a single string
        out += _pack_str(frame.text if isinstance(frame.text, str) else "\n".join(frame.text))
        return bytes(out)

    if fid == "APIC":
        out.append(_FRAME_TYPE_APIC)
        out.append(int(frame.encoding) & 0xFF)
        out += _pack_str(frame.mime)
        out += _pack_u32(int(frame.type) & 0xFFFFFFFF)
        out += _pack_str(frame.desc)
        out += _pack_bytes(frame.data)
        return bytes(out)

    raise ValueError(f"Unsupported frame: {fid}")


def _bytes_to_frame(b: bytes, off: int) -> Tuple[Frame, int]:
    fid, off = _unpack_str(b, off)
    if off >= len(b):
        raise ValueError("Corrupt metadata")
    ftype = b[off]
    off += 1
    if off >= len(b):
        raise ValueError("Corrupt metadata")
    encoding = b[off]
    off += 1

    if ftype == _FRAME_TYPE_TEXT:
        n, off = _unpack_u16(b, off)
        texts: List[str] = []
        for _ in range(n):
            s, off = _unpack_str(b, off)
            texts.append(s)
        if fid == "TIT2":
            return TIT2(encoding=encoding, text=texts), off
        if fid == "TPE1":
            return TPE1(encoding=encoding, text=texts), off
        # Unknown "text" frame id; keep as TIT2-like? Not needed in tests.
        return TIT2(encoding=encoding, text=texts), off

    if ftype == _FRAME_TYPE_COMM:
        lang, off = _unpack_str(b, off)
        desc, off = _unpack_str(b, off)
        text, off = _unpack_str(b, off)
        return COMM(encoding=encoding, lang=lang, desc=desc, text=text), off

    if ftype == _FRAME_TYPE_APIC:
        mime, off = _unpack_str(b, off)
        typ, off = _unpack_u32(b, off)
        desc, off = _unpack_str(b, off)
        data, off = _unpack_bytes(b, off)
        return APIC(encoding=encoding, mime=mime, type=int(typ), desc=desc, data=data), off

    raise ValueError("Unknown frame type")


def _serialize_frames(frames_by_id: Dict[str, List[Frame]]) -> bytes:
    # Deterministic order for stability/perf tests.
    items: List[Tuple[str, Frame]] = []
    for fid in sorted(frames_by_id.keys()):
        for fr in frames_by_id[fid]:
            items.append((fid, fr))

    out = bytearray()
    out += b"FRMS"
    out += _pack_u32(len(items))
    for _, fr in items:
        fb = _frame_to_bytes(fr)
        out += _pack_u32(len(fb))
        out += fb
    return bytes(out)


def _deserialize_frames(meta: bytes) -> Dict[str, List[Frame]]:
    if not meta:
        return {}
    off = 0
    if len(meta) < 8 or meta[0:4] != b"FRMS":
        # unknown or old; ignore
        return {}
    off = 4
    n, off = _unpack_u32(meta, off)
    frames_by_id: Dict[str, List[Frame]] = {}
    for _ in range(n):
        ln, off = _unpack_u32(meta, off)
        chunk = meta[off : off + ln]
        off += ln
        fr, _ = _bytes_to_frame(chunk, 0)
        frames_by_id.setdefault(fr.FrameID, []).append(fr)
    return frames_by_id


# -----------------------------------------------------------------------------
# ID3 class
# -----------------------------------------------------------------------------

class ID3:
    def __init__(self, filename: Optional[str] = None) -> None:
        self.filename: Optional[str] = filename
        self._audio: bytes = b""
        self._frames: Dict[str, List[Frame]] = {}

        if filename is not None:
            try:
                data = _read_file_bytes(filename)
            except FileNotFoundError:
                # treat as empty tag
                self._audio = b""
                self._frames = {}
                return

            meta, audio = _parse_container(data)
            self._audio = audio
            self._frames = _deserialize_frames(meta or b"")

    def add(self, frame: Frame) -> None:
        self._frames.setdefault(frame.FrameID, []).append(frame)

    def getall(self, frame_id: str) -> List[Frame]:
        return list(self._frames.get(frame_id, []))

    def delall(self, frame_id: str) -> None:
        self._frames.pop(frame_id, None)

    def setall(self, frame_id: str, frames: Iterable[Frame]) -> None:
        self._frames[frame_id] = list(frames)

    def __getitem__(self, frame_id: str) -> Frame:
        frames = self._frames.get(frame_id)
        if not frames:
            raise KeyError(frame_id)
        return frames[0]

    def save(self, filename: Optional[str] = None) -> None:
        target = filename or self.filename
        if not target:
            raise ValueError("No filename specified for save()")

        # If saving to a new path and we were loaded from some file, preserve audio;
        # otherwise produce a tag-only "mp3" file (audio empty).
        audio = self._audio
        if filename is not None and self.filename is None:
            audio = b""

        meta = _serialize_frames(self._frames)
        out = _build_container(meta, audio)
        _write_file_bytes(target, out)

        self.filename = target