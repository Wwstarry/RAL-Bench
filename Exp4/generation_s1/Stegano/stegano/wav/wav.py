from __future__ import annotations

from typing import Any, Union
import wave
import struct
from pathlib import Path

from stegano.tools.bititerator import bytes_to_bits, bits_to_bytes
from stegano.tools.utils import frame_payload, parse_length_prefix_from_bits, validate_length_against_capacity_bytes


def _iter_sample_lsbs(frames: bytes, sampwidth: int) -> tuple[list[int], int]:
    """
    Return (samples, count) where samples are integers (already decoded) in
    interleaved channel order.
    """
    if sampwidth == 1:
        # unsigned bytes
        return list(frames), len(frames)
    if sampwidth == 2:
        count = len(frames) // 2
        samples = list(struct.unpack("<" + "h" * count, frames))
        return samples, count
    raise ValueError("Unsupported WAV sample width (only 8-bit or 16-bit PCM supported).")


def _pack_samples(samples: list[int], sampwidth: int) -> bytes:
    if sampwidth == 1:
        return bytes((s & 0xFF) for s in samples)
    if sampwidth == 2:
        return struct.pack("<" + "h" * len(samples), *samples)
    raise ValueError("Unsupported WAV sample width (only 8-bit or 16-bit PCM supported).")


def hide(input_file: Union[str, Path], message: str, output_file: Union[str, Path], **kwargs: Any) -> None:
    payload = frame_payload(message.encode("UTF-8"))
    bits = list(bytes_to_bits(payload))

    with wave.open(str(input_file), "rb") as r:
        params = r.getparams()
        frames = r.readframes(r.getnframes())

    sampwidth = params.sampwidth
    samples, n_samples = _iter_sample_lsbs(frames, sampwidth)

    capacity_bits = n_samples
    if len(bits) > capacity_bits:
        raise ValueError("Message too large to hide in WAV (insufficient capacity).")

    for i, bit in enumerate(bits):
        if sampwidth == 1:
            samples[i] = (samples[i] & 0xFE) | bit
        else:
            samples[i] = (samples[i] & ~1) | bit

    out_frames = _pack_samples(samples, sampwidth)
    with wave.open(str(output_file), "wb") as w:
        w.setparams(params)
        w.writeframes(out_frames)


def reveal(input_file: Union[str, Path], **kwargs: Any) -> str:
    with wave.open(str(input_file), "rb") as r:
        params = r.getparams()
        frames = r.readframes(r.getnframes())

    sampwidth = params.sampwidth
    samples, n_samples = _iter_sample_lsbs(frames, sampwidth)

    def bit_iter():
        for s in samples:
            yield (s & 1)

    it = bit_iter()
    length, length_bits_consumed = parse_length_prefix_from_bits(it)
    remaining_bits = n_samples - length_bits_consumed
    validate_length_against_capacity_bytes(length, remaining_bits)

    payload_bits = [next(it) for _ in range(length * 8)]
    payload = bits_to_bytes(payload_bits)
    return payload.decode("UTF-8")