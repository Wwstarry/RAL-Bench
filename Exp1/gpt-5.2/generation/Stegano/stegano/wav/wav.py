from __future__ import annotations

from typing import Any, Optional

import wave

from stegano.tools.bititerator import bits_from_bytes, bytes_from_bits
from stegano.tools.utils import text_to_bytes, bytes_to_text


_SENTINEL = b"\x00\xffWAVSTEG\xff\x00"
_LEN_BYTES = 4


def _read_wave_params_and_frames(path: str):
    with wave.open(path, "rb") as w:
        params = w.getparams()
        frames = w.readframes(w.getnframes())
    return params, bytearray(frames)


def _write_wave(path: str, params, frames: bytes):
    with wave.open(path, "wb") as w:
        w.setparams(params)
        w.writeframes(frames)


def hide(
    input_file: str,
    message: str,
    output_file: str,
    encoding: str = "UTF-8",
    **kwargs: Any,
) -> None:
    """
    Hide a text message into PCM WAV by setting LSB of each frame byte.
    Writes output_file.
    """
    params, frames = _read_wave_params_and_frames(input_file)

    # Only PCM uncompressed is expected by wave module; sampwidth 1/2/3/4 supported.
    payload = text_to_bytes(message, encoding=encoding)
    framed = _SENTINEL + int.to_bytes(len(payload), _LEN_BYTES, "big") + payload
    bits = list(bits_from_bytes(framed))

    capacity = len(frames)
    if len(bits) > capacity:
        raise ValueError("Message too large for WAV capacity")

    for i, b in enumerate(bits):
        frames[i] = (frames[i] & 0xFE) | (b & 1)

    _write_wave(output_file, params, bytes(frames))


def reveal(
    input_file: str,
    encoding: str = "UTF-8",
    **kwargs: Any,
) -> str:
    """
    Reveal a hidden text message from PCM WAV. Returns decoded text.
    """
    params, frames = _read_wave_params_and_frames(input_file)

    header_len = len(_SENTINEL) + _LEN_BYTES
    header_bits = header_len * 8
    if header_bits > len(frames):
        raise ValueError("No hidden message found")

    header_bit_list = [(frames[i] & 1) for i in range(header_bits)]
    header = bytes(bytes_from_bits(iter(header_bit_list)))

    if not header.startswith(_SENTINEL):
        raise ValueError("No hidden message found")

    msg_len = int.from_bytes(header[len(_SENTINEL):len(_SENTINEL) + _LEN_BYTES], "big")
    msg_bits = msg_len * 8
    total_bits = header_bits + msg_bits
    if total_bits > len(frames):
        raise ValueError("Malformed message")

    msg_bit_list = [(frames[i] & 1) for i in range(header_bits, total_bits)]
    msg_bytes = bytes(bytes_from_bits(iter(msg_bit_list)))
    return bytes_to_text(msg_bytes, encoding=encoding)