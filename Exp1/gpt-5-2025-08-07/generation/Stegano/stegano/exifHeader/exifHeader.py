from typing import Optional, Union
from PIL import Image, TiffImagePlugin

def _as_bytes(secret_message: Union[bytes, str], encoding: Optional[str]) -> bytes:
    if isinstance(secret_message, bytes):
        return secret_message
    if encoding is None:
        encoding = "UTF-8"
    return str(secret_message).encode(encoding, errors="strict")

def hide(input_image_file, output_path, secret_message: Union[bytes, str] = b"", encoding: Optional[str] = "UTF-8") -> None:
    """
    Hide a byte message in the image metadata.
    - For JPEG: stored in COM (comment) segment.
    - For TIFF: stored in tag 270 (ImageDescription).
    Writes the image to output_path.
    """
    msg_bytes = _as_bytes(secret_message, encoding)
    with Image.open(input_image_file) as im:
        fmt = (im.format or "").upper()
        if fmt == "JPEG":
            # Write COM marker with comment bytes
            im.save(output_path, format="JPEG", comment=msg_bytes)
        elif fmt == "TIFF":
            # Store in ImageDescription tag
            tiffinfo = TiffImagePlugin.ImageFileDirectory_v2()
            # Tag 270: ImageDescription. It commonly stores ASCII; we store bytes as is.
            try:
                # If bytes not acceptable directly, convert to latin1 string mapping 0-255 to same codes
                desc = msg_bytes.decode("latin1")
                tiffinfo[270] = desc
            except Exception:
                tiffinfo[270] = msg_bytes
            im.save(output_path, format="TIFF", tiffinfo=tiffinfo)
        else:
            # Fallback: save copy with a "comment" if supported (e.g., PNG text)
            # PNG supports "pnginfo", but to keep dependencies minimal, attempt save with info dict.
            # Pillow will ignore unsupported keys.
            im.info["comment"] = msg_bytes
            im.save(output_path)

def reveal(image) -> bytes:
    """
    Reveal the hidden message from metadata.
    - For JPEG: read COM (comment).
    - For TIFF: read tag 270 (ImageDescription).
    Returns raw bytes.
    """
    with Image.open(image) as im:
        fmt = (im.format or "").upper()
        if fmt == "JPEG":
            comment = im.info.get("comment", b"")
            if isinstance(comment, str):
                return comment.encode("latin1", errors="replace")
            return comment or b""
        elif fmt == "TIFF":
            # Read ImageDescription tag
            try:
                tag_v2 = getattr(im, "tag_v2", None)
                if tag_v2 is not None:
                    val = tag_v2.get(270, "")
                    if isinstance(val, bytes):
                        return val
                    if isinstance(val, str):
                        return val.encode("latin1", errors="replace")
                    # Sometimes tag_v2.get returns a list
                    if isinstance(val, (list, tuple)) and val:
                        v0 = val[0]
                        if isinstance(v0, bytes):
                            return v0
                        if isinstance(v0, str):
                            return v0.encode("latin1", errors="replace")
                # Fallback to traditional tag dict
                tag = getattr(im, "tag", None)
                if tag is not None:
                    val = tag.get(270)
                    if isinstance(val, bytes):
                        return val
                    if isinstance(val, str):
                        return val.encode("latin1", errors="replace")
            except Exception:
                pass
            return b""
        else:
            # Fallback: try info["comment"]
            comment = im.info.get("comment", b"")
            if isinstance(comment, str):
                return comment.encode("latin1", errors="replace")
            return comment or b""