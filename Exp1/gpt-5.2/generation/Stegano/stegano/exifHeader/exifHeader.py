from __future__ import annotations

from typing import Any, Optional, Union

from PIL import Image
from PIL.ExifTags import Base as ExifBase

from stegano.tools.utils import ensure_image


# We'll store bytes in EXIF UserComment if possible; fallback to ImageDescription.
# UserComment is a standard tag (37510). ImageDescription is 270.
_USER_COMMENT = 37510
_IMAGE_DESCRIPTION = 270

_SENTINEL = b"STEGANO_EXIF\0"
_LEN_BYTES = 4


def hide(
    input_image_file: Union[str, Image.Image],
    output_path: str,
    secret_message: bytes = b"",
    **kwargs: Any,
) -> None:
    """
    Embed bytes in EXIF metadata and write to output_path.

    The reference project supports additional kwargs; we accept and ignore them
    for compatibility.
    """
    img = ensure_image(input_image_file)

    payload = bytes(secret_message)
    framed = _SENTINEL + int.to_bytes(len(payload), _LEN_BYTES, "big") + payload

    exif = img.getexif()
    if exif is None:
        exif = Image.Exif()

    # Prefer UserComment for binary-ish data. Pillow stores values as bytes or str.
    exif[_USER_COMMENT] = framed

    # Also set ImageDescription to a small marker for broader compatibility.
    try:
        exif[_IMAGE_DESCRIPTION] = "stegano"
    except Exception:
        pass

    save_kwargs = {}
    # If JPEG, keep quality if provided
    if "quality" in kwargs:
        save_kwargs["quality"] = kwargs["quality"]
    if "subsampling" in kwargs:
        save_kwargs["subsampling"] = kwargs["subsampling"]
    if "optimize" in kwargs:
        save_kwargs["optimize"] = kwargs["optimize"]

    img.save(output_path, exif=exif, **save_kwargs)


def _extract_framed(exif: Image.Exif) -> Optional[bytes]:
    if exif is None:
        return None
    val = exif.get(_USER_COMMENT)
    if val is None:
        val = exif.get(_IMAGE_DESCRIPTION)
        if val is None:
            return None
        if isinstance(val, str):
            val = val.encode("utf-8", errors="ignore")
    if isinstance(val, str):
        val = val.encode("utf-8", errors="ignore")
    if not isinstance(val, (bytes, bytearray)):
        try:
            val = bytes(val)
        except Exception:
            return None
    return bytes(val)


def reveal(image: Union[str, Image.Image]) -> bytes:
    """
    Extract bytes from EXIF metadata. Returns raw bytes message.
    """
    img = ensure_image(image)
    exif = img.getexif()
    framed = _extract_framed(exif)
    if not framed:
        raise ValueError("No hidden message found")

    if not framed.startswith(_SENTINEL) or len(framed) < len(_SENTINEL) + _LEN_BYTES:
        raise ValueError("No hidden message found")

    msg_len = int.from_bytes(
        framed[len(_SENTINEL):len(_SENTINEL) + _LEN_BYTES], "big", signed=False
    )
    start = len(_SENTINEL) + _LEN_BYTES
    end = start + msg_len
    if end > len(framed):
        raise ValueError("Malformed message")
    return framed[start:end]