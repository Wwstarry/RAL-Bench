import io
import os
import struct
from typing import List, Dict, Optional, Iterable


def _u32be(n: int) -> bytes:
    return struct.pack(">I", int(n))


def _read_u32be(b: bytes) -> int:
    return struct.unpack(">I", b)[0]


def _is_frame_id(fid: bytes) -> bool:
    # Basic validation: uppercase letters/numbers, length 4
    if len(fid) != 4:
        return False
    try:
        s = fid.decode("ascii")
    except Exception:
        return False
    return all(("A" <= c <= "Z") or ("0" <= c <= "9") for c in s)


def _encode_text(encoding: int, texts: List[str]) -> bytes:
    if texts is None:
        texts = []
    # join list into single bytes with null separators for multi values
    if encoding == 0:
        joined = "\x00".join(texts)
        return b"\x00" + joined.encode("latin1", "replace")
    elif encoding == 3:
        joined = "\x00".join(texts)
        return b"\x03" + joined.encode("utf-8")
    else:
        # fallback to utf-8 marker (3)
        joined = "\x00".join(texts)
        return b"\x03" + joined.encode("utf-8")


def _decode_text(encoding: int, data: bytes) -> List[str]:
    if encoding == 0:
        s = data.decode("latin1", "replace")
    elif encoding == 3:
        s = data.decode("utf-8", "replace")
    else:
        # fallback: utf-8
        try:
            s = data.decode("utf-8", "replace")
        except Exception:
            s = data.decode("latin1", "replace")
    # split on null to recover multiple values
    return s.split("\x00")


def _encode_comm(encoding: int, lang: str, desc: str, text: str) -> bytes:
    if not isinstance(lang, str):
        lang = "eng"
    lang_bytes = (lang[:3].ljust(3, "\x00")).encode("ascii", "replace")
    if encoding == 0:
        desc_bytes = desc.encode("latin1", "replace") + b"\x00"
        text_bytes = text.encode("latin1", "replace")
        return b"\x00" + lang_bytes + desc_bytes + text_bytes
    else:
        # Use utf-8 (3)
        desc_bytes = desc.encode("utf-8") + b"\x00"
        text_bytes = text.encode("utf-8")
        return b"\x03" + lang_bytes + desc_bytes + text_bytes


def _decode_comm(data: bytes):
    if not data:
        return (3, "eng", "", "")
    encoding = data[0]
    lang = data[1:4].decode("ascii", "replace")
    rest = data[4:]
    # description terminated by null byte
    idx = rest.find(b"\x00")
    if idx == -1:
        desc_bytes = rest
        text_bytes = b""
    else:
        desc_bytes = rest[:idx]
        text_bytes = rest[idx + 1 :]
    if encoding == 0:
        desc = desc_bytes.decode("latin1", "replace")
        text = text_bytes.decode("latin1", "replace")
    elif encoding == 3:
        desc = desc_bytes.decode("utf-8", "replace")
        text = text_bytes.decode("utf-8", "replace")
    else:
        # fallback
        try:
            desc = desc_bytes.decode("utf-8")
            text = text_bytes.decode("utf-8")
        except Exception:
            desc = desc_bytes.decode("latin1", "replace")
            text = text_bytes.decode("latin1", "replace")
    return (encoding, lang, desc, text)


def _encode_apic(encoding: int, mime: str, type_: int, desc: str, data: bytes) -> bytes:
    if not isinstance(mime, str):
        mime = "application/octet-stream"
    mime_bytes = mime.encode("ascii", "replace") + b"\x00"
    type_byte = bytes([int(type_) & 0xFF])
    if encoding == 0:
        desc_bytes = desc.encode("latin1", "replace") + b"\x00"
        prefix = b"\x00"
    else:
        desc_bytes = desc.encode("utf-8") + b"\x00"
        prefix = b"\x03"
    return prefix + mime_bytes + type_byte + desc_bytes + (data or b"")


def _decode_apic(data: bytes):
    if not data:
        return (3, "application/octet-stream", 0, "", b"")
    encoding = data[0]
    # MIME up to first null
    idx_mime_end = data.find(b"\x00", 1)
    if idx_mime_end == -1:
        mime = "application/octet-stream"
        type_pos = 1
    else:
        mime = data[1:idx_mime_end].decode("ascii", "replace")
        type_pos = idx_mime_end + 1
    if type_pos >= len(data):
        type_ = 0
        desc_start = type_pos
    else:
        type_ = data[type_pos]
        desc_start = type_pos + 1
    # desc terminated by null
    rest = data[desc_start:]
    idx_desc_end = rest.find(b"\x00")
    if idx_desc_end == -1:
        desc_bytes = rest
        pic_data = b""
    else:
        desc_bytes = rest[:idx_desc_end]
        pic_data = rest[idx_desc_end + 1 :]
    if encoding == 0:
        try:
            desc = desc_bytes.decode("latin1", "replace")
        except Exception:
            desc = ""
    elif encoding == 3:
        try:
            desc = desc_bytes.decode("utf-8", "replace")
        except Exception:
            desc = ""
    else:
        try:
            desc = desc_bytes.decode("utf-8", "replace")
        except Exception:
            desc = ""
    return (encoding, mime, type_, desc, pic_data)


class Frame:
    frame_id = "----"

    @property
    def id(self) -> str:
        return self.frame_id

    def _render(self) -> bytes:
        raise NotImplementedError


class TextFrame(Frame):
    def __init__(self, encoding: int = 3, text: Optional[Iterable[str]] = None):
        self.encoding = int(encoding) if encoding is not None else 3
        if text is None:
            self.text: List[str] = []
        elif isinstance(text, (str, bytes)):
            # Single string
            if isinstance(text, bytes):
                try:
                    text = text.decode("utf-8")
                except Exception:
                    text = text.decode("latin1", "replace")
            self.text = [text]
        else:
            # Iterable of strings
            self.text = [str(t) for t in text]

    def _render(self) -> bytes:
        data = _encode_text(self.encoding, self.text)
        return data


class TIT2(TextFrame):
    frame_id = "TIT2"


class TPE1(TextFrame):
    frame_id = "TPE1"


class TRCK(TextFrame):
    frame_id = "TRCK"


class COMM(Frame):
    frame_id = "COMM"

    def __init__(self, encoding: int = 3, lang: str = "eng", desc: str = "", text: str = ""):
        self.encoding = int(encoding) if encoding is not None else 3
        self.lang = str(lang or "eng")[:3]
        self.desc = str(desc or "")
        self.text = str(text or "")

    def _render(self) -> bytes:
        return _encode_comm(self.encoding, self.lang, self.desc, self.text)


class APIC(Frame):
    frame_id = "APIC"

    def __init__(self, encoding: int = 3, mime: str = "application/octet-stream", type: int = 0, desc: str = "", data: bytes = b""):
        self.encoding = int(encoding) if encoding is not None else 3
        self.mime = str(mime or "application/octet-stream")
        self.type = int(type or 0)
        self.desc = str(desc or "")
        # Ensure bytes
        if not isinstance(data, (bytes, bytearray)):
            data = bytes(data)
        self.data = bytes(data)

    def _render(self) -> bytes:
        return _encode_apic(self.encoding, self.mime, self.type, self.desc, self.data)


FRAME_CLASSES: Dict[str, type] = {
    "TIT2": TIT2,
    "TPE1": TPE1,
    "TRCK": TRCK,
    "COMM": COMM,
    "APIC": APIC,
}


class ID3:
    def __init__(self, path: Optional[str] = None):
        self._frames: Dict[str, List[Frame]] = {}
        self._path: Optional[str] = None
        if path is not None:
            self.load(path)

    def load(self, path: str):
        self._path = path
        self._frames.clear()
        try:
            with open(path, "rb") as f:
                data = f.read()
        except FileNotFoundError:
            return
        if not data or len(data) < 10:
            return
        if data[:3] != b"ID3":
            # Not an ID3 tag-only file written by us; ignore for simplicity.
            return
        # Header: "ID3", version bytes, flags, size (we use non-syncsafe >I)
        # We ignore header size and parse frames sequentially.
        pos = 10
        end = len(data)
        while pos + 10 <= end:
            fid = data[pos : pos + 4]
            if fid == b"\x00\x00\x00\x00" or not _is_frame_id(fid):
                break
            size = _read_u32be(data[pos + 4 : pos + 8])
            # flags = data[pos + 8 : pos + 10]
            pos += 10
            if pos + size > end:
                # invalid size; stop
                break
            payload = data[pos : pos + size]
            pos += size
            fid_str = fid.decode("ascii")
            frame = None
            try:
                if fid_str in ("TIT2", "TPE1", "TRCK"):
                    if len(payload) == 0:
                        continue
                    enc = payload[0]
                    texts = _decode_text(enc, payload[1:])
                    cls = FRAME_CLASSES[fid_str]
                    frame = cls(encoding=enc, text=texts)
                elif fid_str == "COMM":
                    enc, lang, desc, text = _decode_comm(payload)
                    frame = COMM(encoding=enc, lang=lang, desc=desc, text=text)
                elif fid_str == "APIC":
                    enc, mime, type_, desc, imgdata = _decode_apic(payload)
                    frame = APIC(encoding=enc, mime=mime, type=type_, desc=desc, data=imgdata)
                else:
                    # unsupported; ignore
                    frame = None
            except Exception:
                frame = None
            if frame is not None:
                self.add(frame)

    def add(self, frame: Frame):
        fid = frame.id
        self._frames.setdefault(fid, []).append(frame)

    def __getitem__(self, frame_id: str) -> Frame:
        frames = self._frames.get(frame_id)
        if not frames:
            raise KeyError(frame_id)
        return frames[0]

    def getall(self, frame_id: str) -> List[Frame]:
        return list(self._frames.get(frame_id, []))

    def delall(self, frame_id: str):
        if frame_id in self._frames:
            del self._frames[frame_id]

    def setall(self, frame_id: str, frames: Iterable[Frame]):
        # Replace any existing set for frame_id
        self._frames[frame_id] = [f for f in frames]

    def save(self, path: Optional[str] = None):
        if path is None:
            path = self._path
        if not path:
            raise ValueError("No path specified for saving ID3 tags")
        # Encode frames
        out = io.BytesIO()
        # Placeholder header
        # ID3 v2.4.0, flags 0, size to be filled after frames encoded
        out.write(b"ID3")
        out.write(bytes([4, 0, 0]))
        out.write(_u32be(0))  # placeholder for size

        # Write frames
        content = io.BytesIO()
        for fid, frames in self._frames.items():
            for frame in frames:
                payload = frame._render()
                # Frame header: id, 4-byte size, 2-byte flags
                content.write(fid.encode("ascii"))
                content.write(_u32be(len(payload)))
                content.write(b"\x00\x00")
                content.write(payload)
        frames_bytes = content.getvalue()
        out_size = len(frames_bytes)
        out.seek(6)
        out.write(_u32be(out_size))
        out.seek(0, io.SEEK_END)
        out.write(frames_bytes)
        data = out.getvalue()
        # Write to file
        with open(path, "wb") as f:
            f.write(data)
        self._path = path

    def __contains__(self, frame_id: str) -> bool:
        return frame_id in self._frames

    def keys(self) -> Iterable[str]:
        return self._frames.keys()

    def items(self):
        return self._frames.items()

    def values(self):
        return self._frames.values()