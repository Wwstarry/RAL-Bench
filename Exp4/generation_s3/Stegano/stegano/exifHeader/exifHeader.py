from __future__ import annotations

import base64
from typing import Any, Union

from PIL import Image, TiffImagePlugin

from stegano.tools.utils import ensure_image

ImageInput = Union[str, Image.Image]

# We store in EXIF UserComment (37510) as ASCII with a prefix for identification.
_TAG_USER_COMMENT = 37510
_PREFIX = b"STEGANO_EXIF_B64:"


def _get_exif_dict(img: Image.Image) -> dict[int, Any]:
    exif = img.getexif()
    # PIL Exif object behaves like a dict; convert to plain dict for manipulation.
    return {int(k): exif.get(k) for k in exif.keys()}


def hide(
    input_image_file: str,
    output_path: str,
    secret_message: bytes = b"",
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Embed arbitrary bytes into EXIF metadata and write to output_path.

    Accepts extra args/kwargs for compatibility; they are ignored.
    """
    if not isinstance(secret_message, (bytes, bytearray)):
        raise TypeError("secret_message must be bytes")

    img = Image.open(input_image_file)
    exif_dict = _get_exif_dict(img)

    b64 = base64.b64encode(bytes(secret_message))
    value = _PREFIX + b64

    # Store as bytes; PIL will marshal appropriately for EXIF.
    exif_dict[_TAG_USER_COMMENT] = value

    exif = Image.Exif()
    for k, v in exif_dict.items():
        try:
            exif[k] = v
        except Exception:
            # If some tags cannot be set, ignore them; our tag is the important one.
            pass
    exif[_TAG_USER_COMMENT] = value

    save_kwargs: dict[str, Any] = {"exif": exif.tobytes()}
    # Preserve format if possible; PIL chooses from output extension.
    img.save(output_path, **save_kwargs)


def reveal(image: ImageInput) -> bytes:
    img = ensure_image(image)
    exif = img.getexif()
    if not exif:
        raise ValueError("No EXIF metadata found.")

    raw = exif.get(_TAG_USER_COMMENT)
    if raw is None:
        raise ValueError("No hidden message found in EXIF metadata.")

    # raw might be bytes, str, or a tuple depending on PIL/version; normalize.
    if isinstance(raw, str):
        raw_bytes = raw.encode("utf-8", errors="ignore")
    elif isinstance(raw, (bytes, bytearray)):
        raw_bytes = bytes(raw)
    elif isinstance(raw, (tuple, list)):
        # Some representations return a sequence of ints
        try:
            raw_bytes = bytes(raw)
        except Exception as e:
            raise ValueError("Unsupported EXIF UserComment type.") from e
    else:
        raise ValueError("Unsupported EXIF UserComment type.")

    if not raw_bytes.startswith(_PREFIX):
        raise ValueError("No hidden message found in EXIF metadata.")

    b64 = raw_bytes[len(_PREFIX) :]
    try:
        return base64.b64decode(b64, validate=False)
    except Exception as e:
        raise ValueError("Corrupted hidden message in EXIF metadata.") from e