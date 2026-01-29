from __future__ import annotations

import wave
from typing import Any, Optional

from stegano.tools.bititerator import bits_from_bytes, bytes_from_bits
from stegano.tools.utils import DEFAULT_TERMINATOR, find_terminator_index


def hide(
    input_file: str,
    message: str,
    output_file: str,
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Hide a text message in the LSB of PCM WAV samples and write output_file.

    Accepted kwargs (optional):
      - encoding: str (default "UTF-8")
      - num_lsb: int (default 1)  [currently only 1 supported]
    """
    encoding = kwargs.get("encoding", "UTF-8")
    num_lsb = int(kwargs.get("num_lsb", 1))
    if num_lsb != 1:
        raise ValueError("Only num_lsb=1 is supported in this implementation.")

    payload = message.encode(encoding) + DEFAULT_TERMINATOR
    bits = list(bits_from_bytes(payload))

    with wave.open(input_file, "rb") as r:
        params = r.getparams()
        frames = r.readframes(r.getnframes())

    # We embed into the least significant bit of each byte of the raw frame data.
    # This works for common PCM encodings and preserves container parameters.
    capacity_bits = len(frames)  # 1 bit per byte
    if len(bits) > capacity_bits:
        raise ValueError("Insufficient capacity to hide message in WAV file.")

    frame_bytes = bytearray(frames)
    for i, bit in enumerate(bits):
        frame_bytes[i] = (frame_bytes[i] & 0xFE) | bit

    with wave.open(output_file, "wb") as w:
        w.setparams(params)
        w.writeframes(bytes(frame_bytes))


def reveal(
    input_file: str,
    *args: Any,
    **kwargs: Any,
) -> str:
    """
    Reveal a text message hidden in the LSB of PCM WAV samples.

    Accepted kwargs (optional):
      - encoding: str (default "UTF-8")
      - num_lsb: int (default 1)  [currently only 1 supported]
    """
    encoding = kwargs.get("encoding", "UTF-8")
    num_lsb = int(kwargs.get("num_lsb", 1))
    if num_lsb != 1:
        raise ValueError("Only num_lsb=1 is supported in this implementation.")

    with wave.open(input_file, "rb") as r:
        frames = r.readframes(r.getnframes())

    bits = []
    collected = bytearray()

    for b in frames:
        bits.append(b & 1)
        if len(bits) == 8:
            collected.extend(bytes_from_bits(bits))
            bits.clear()
            idx = find_terminator_index(collected, DEFAULT_TERMINATOR)
            if idx != -1:
                data = bytes(collected[:idx])
                return data.decode(encoding)

    raise ValueError("No hidden message found (terminator not present).")