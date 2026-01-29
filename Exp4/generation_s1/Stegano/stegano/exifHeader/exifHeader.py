from __future__ import annotations

from typing import Any, Union
from pathlib import Path

from PIL import Image

from stegano.tools.utils import ensure_image, uint32be_pack, uint32be_unpack

_USERCOMMENT_TAG = 37510  # EXIF UserComment
_MAGIC = b"STEGANO\x00"


def _normalize_bytes(value: Any) -> bytes:
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("latin1", errors="ignore")
    # Pillow may return an Exif "IFDRational" etc; coerce
    try:
        return bytes(value)
    except Exception:
        return b""


def hide(input_image_file: Union[str, Path, Any], output_path: Union[str, Path], secret_message: bytes = b"", **kwargs: Any) -> None:
    """
    Embed secret_message bytes into EXIF UserComment. Writes output_path.
    Extra kwargs are accepted and ignored for compatibility.
    """
    if isinstance(secret_message, str):
        secret_message = secret_message.encode("UTF-8")

    img = Image.open(input_image_file)
    exif = img.getexif()
    payload = _MAGIC + uint32be_pack(len(secret_message)) + secret_message

    # Try bytes first; if Pillow rejects, fall back to latin1 string roundtrip.
    try:
        exif[_USERCOMMENT_TAG] = payload
        exif_bytes = exif.tobytes()
    except Exception:
        exif[_USERCOMMENT_TAG] = payload.decode("latin1", errors="ignore")
        exif_bytes = exif.tobytes()

    img.save(output_path, exif=exif_bytes)


def reveal(image: Union[str, Path, Image.Image, Any]) -> bytes:
    img = ensure_image(image) if isinstance(image, Image.Image) else Image.open(image)
    exif = img.getexif()
    raw = _normalize_bytes(exif.get(_USERCOMMENT_TAG))
    if not raw.startswith(_MAGIC):
        return b""
    if len(raw) < len(_MAGIC) + 4:
        return b""
    length = uint32be_unpack(raw[len(_MAGIC): len(_MAGIC) + 4])
    data = raw[len(_MAGIC) + 4:]
    if length > len(data):
        return b""
    return data[:length]