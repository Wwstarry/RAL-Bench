from __future__ import annotations

from typing import Optional, Union

import piexif
from PIL import Image

from stegano.tools.utils import ensure_image

_USER_COMMENT = piexif.ExifIFD.UserComment
_MAGIC_PREFIX = b"STEGANO_EXIF\0"


def hide(
    input_image_file,
    output_path,
    secret_message: Union[bytes, bytearray] = b"",
    encoding: str = "utf-8",
    **kwargs,
):
    """
    Embed bytes into EXIF UserComment for JPEG/TIFF-like formats.
    Writes the modified image to output_path.

    Signature is intentionally permissive with **kwargs for compatibility.
    """
    # input_image_file can be a path or a PIL image.
    if isinstance(input_image_file, Image.Image):
        img = input_image_file
        src_path = None
    else:
        src_path = input_image_file
        img = Image.open(input_image_file)

    msg = bytes(secret_message) if not isinstance(secret_message, bytes) else secret_message

    # Load existing exif (if any)
    exif_bytes = img.info.get("exif", b"")
    try:
        exif_dict = piexif.load(exif_bytes) if exif_bytes else {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
    except Exception:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}

    exif_dict.setdefault("Exif", {})
    exif_dict["Exif"][_USER_COMMENT] = _MAGIC_PREFIX + msg
    new_exif = piexif.dump(exif_dict)

    # Preserve format if possible; default to JPEG if unknown
    fmt = img.format or (Image.open(src_path).format if src_path else None) or "JPEG"
    save_kwargs = {}
    if fmt.upper() in ("JPEG", "JPG", "TIFF"):
        save_kwargs["exif"] = new_exif
    else:
        # Pillow supports EXIF mostly for JPEG/TIFF. Still attempt to save with exif.
        save_kwargs["exif"] = new_exif

    img.save(output_path, format=fmt, **save_kwargs)


def reveal(image) -> bytes:
    """
    Extract bytes from EXIF UserComment.
    Accepts a path or PIL.Image.Image.
    """
    img = ensure_image(image)
    exif_bytes = img.info.get("exif", b"")
    if not exif_bytes:
        raise ValueError("No EXIF data found.")

    exif_dict = piexif.load(exif_bytes)
    exif = exif_dict.get("Exif", {})
    raw = exif.get(_USER_COMMENT, None)
    if raw is None:
        raise ValueError("No hidden message found in EXIF UserComment.")

    if isinstance(raw, tuple):
        raw = bytes(raw)
    if not isinstance(raw, (bytes, bytearray)):
        raw = bytes(raw)

    raw = bytes(raw)
    if not raw.startswith(_MAGIC_PREFIX):
        raise ValueError("No hidden message found (missing magic prefix).")

    return raw[len(_MAGIC_PREFIX) :]