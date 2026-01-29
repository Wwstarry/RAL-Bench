"""
stegano.exifHeader – Stores secret bytes inside the EXIF *UserComment* tag.

Only JPEG and TIFF images are supported by Pillow for writing EXIF data.
"""
from __future__ import annotations

from pathlib import Path
from typing import Union

from PIL import Image, TiffImagePlugin


# EXIF tag for *UserComment* – see EXIF specification
USERCOMMENT_TAG = 0x9286


def _ensure_parent_dir(path: Union[str, Path]) -> None:
    path = Path(path)
    if path.parent:
        path.parent.mkdir(parents=True, exist_ok=True)


def hide(
    input_image_file: Union[str, Path],
    output_path: Union[str, Path],
    secret_message: bytes,
) -> None:
    """
    Embeds *secret_message* into EXIF UserComment of *input_image_file* and
    writes the modified image data to *output_path*.
    """
    with Image.open(input_image_file) as im:
        exif = im.getexif()
        exif[USERCOMMENT_TAG] = secret_message
        _ensure_parent_dir(output_path)
        im.save(output_path, exif=exif)


def reveal(image_file: Union[str, Path]) -> bytes:
    """
    Retrieves a byte string from the EXIF UserComment tag.  Returns ``b""`` if
    the tag is missing.
    """
    with Image.open(image_file) as im:
        exif = im.getexif()
        data = exif.get(USERCOMMENT_TAG, b"")
        # Pillow may return a 'bytes' or str depending on the encoder.
        if isinstance(data, str):
            data = data.encode("utf-8", "surrogatepass")
        return data