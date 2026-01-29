"""
Naive EXIF header steganography that inserts a custom APP1 segment
containing the secret data. This may overwrite the existing EXIF data
or create a new segment. In practice you'd want a more robust approach.
"""
import struct

APP1_MARKER = b"\xff\xe1"
CUSTOM_TAG = b"STEGANO"


def hide(input_image_file, output_path, secret_message: bytes = b"", **kwargs):
    """
    Hide secret_message in a new APP1 segment inside the JPEG/TIFF file.
    Writes a new file at output_path.
    :param input_image_file: path to the cover image file (JPEG/TIFF).
    :param output_path: output file path.
    :param secret_message: bytes to embed in the EXIF header area.
    :param kwargs: additional arguments (ignored for compatibility).
    """
    with open(input_image_file, "rb") as f:
        original = f.read()

    # We'll insert a custom APP1 segment after the SOI marker (0xFFD8).
    # Format: 0xFFE1 + length(2 bytes) + "Exif\0\0" + CUSTOM_TAG + length + data
    if not (original[0:2] == b"\xff\xd8"):
        # If it's not a JPEG, we won't do anything fancy, just write as is (for TIFF you'd parse accordingly)
        with open(output_path, "wb") as out:
            out.write(original)
        return

    # Build custom segment
    data_len = len(secret_message)
    # "Exif\0\0" => standard ID. We'll put CUSTOM_TAG + length + secret
    segment_data = b"Exif\0\0" + CUSTOM_TAG + struct.pack(">I", data_len) + secret_message
    segment_total_length = len(segment_data) + 2  # 2 bytes for length field itself
    app1_segment = APP1_MARKER + struct.pack(">H", segment_total_length) + segment_data

    # Insert it right after SOI (FFD8)
    # We'll look for the second marker after FFD8 and insert just before it.
    # If none found, we'll just append.
    # For naive approach, let's just place it right after the first 2 bytes.
    soi = original[:2]
    rest = original[2:]

    # We try to see if there's already an APP0 or something
    # For simplicity, just do soi + app1_segment + rest
    new_data = soi + app1_segment + rest

    with open(output_path, "wb") as out:
        out.write(new_data)


def reveal(image) -> bytes:
    """
    Reveal the hidden bytes from a custom APP1 segment in a JPEG/TIFF file.
    :param image: path to the image file (JPEG/TIFF).
    :return: The hidden bytes or empty if not found.
    """
    with open(image, "rb") as f:
        data = f.read()

    # Check for custom APP1 marker
    offset = 2  # skip SOI
    while offset < len(data):
        if data[offset:offset+2] == b"\xff\xd9":
            # End of file
            break
        if data[offset:offset+2] == APP1_MARKER:
            # Found APP1
            length_bytes = data[offset+2:offset+4]
            seg_len = struct.unpack(">H", length_bytes)[0]
            segment = data[offset+4:offset+4+seg_len-2]  # seg_len includes the two bytes for length

            # Check if it starts with "Exif\0\0" + CUSTOM_TAG
            if segment.startswith(b"Exif\0\0" + CUSTOM_TAG):
                # read length
                after_tag = segment[len(b"Exif\0\0"+CUSTOM_TAG):]
                if len(after_tag) < 4:
                    return b""
                msg_len = struct.unpack(">I", after_tag[:4])[0]
                secret = after_tag[4:4+msg_len]
                return secret

            offset += 4 + seg_len - 2
        else:
            offset += 1
    return b""