from __future__ import annotations

import wave
from typing import Optional, Union

from stegano.tools.bititerator import bits_from_bytes, bytes_from_bits

_SENTINEL = b"\x00\xff\x00\xff\x00"
_HEADER_LEN = 4 + len(_SENTINEL)


def hide(
    input_file,
    message,
    output_file,
    encoding: str = "utf-8",
    **kwargs,
):
    """
    Hide a message in a PCM WAV file by replacing the LSB of each audio byte.

    Writes the modified audio to output_file.
    """
    if isinstance(message, str):
        payload = message.encode(encoding)
    else:
        payload = bytes(message)

    header = int.to_bytes(len(payload), 4, "big") + _SENTINEL
    data = header + payload
    bits = list(bits_from_bytes(data))

    with wave.open(input_file, "rb") as w:
        params = w.getparams()
        frames = w.readframes(w.getnframes())

    frame_bytes = bytearray(frames)
    capacity = len(frame_bytes)  # 1 bit per byte
    if len(bits) > capacity:
        raise ValueError("Message too large to hide in WAV file.")

    for i, bit in enumerate(bits):
        frame_bytes[i] = (frame_bytes[i] & 0xFE) | (1 if bit else 0)

    with wave.open(output_file, "wb") as wout:
        wout.setparams(params)
        wout.writeframes(bytes(frame_bytes))


def reveal(
    input_file,
    encoding: str = "utf-8",
    **kwargs,
) -> str:
    """
    Reveal a message hidden by stegano.wav.hide.
    """
    with wave.open(input_file, "rb") as w:
        frames = w.readframes(w.getnframes())

    frame_bytes = frames  # bytes
    bits_iter = ((b & 1) for b in frame_bytes)

    header_bits = [next(bits_iter) for _ in range(_HEADER_LEN * 8)]
    header = bytes(bytes_from_bits(header_bits))

    msg_len = int.from_bytes(header[:4], "big", signed=False)
    if header[4:] != _SENTINEL:
        raise ValueError("No hidden message found (invalid sentinel).")

    msg_bits = [next(bits_iter) for _ in range(msg_len * 8)]
    msg = bytes(bytes_from_bits(msg_bits))
    return msg.decode(encoding, errors="strict")