"""
stegano.wav – Least-significant-bit steganography for PCM wave files.
"""
from __future__ import annotations

import wave
from pathlib import Path
from typing import Union

from ..tools.utils import bits_from_bytes, bytes_from_bits


def _read_frames(path: Union[str, Path]) -> tuple[bytes, wave._wave_params]:
    with wave.open(str(path), "rb") as wf:
        params = wf.getparams()
        frames = wf.readframes(params.nframes)
    return frames, params


def _write_frames(
    path: Union[str, Path], frames: bytes, params: wave._wave_params
) -> None:
    with wave.open(str(path), "wb") as wf:
        wf.setparams(params)
        wf.writeframes(frames)


def hide(
    input_file: Union[str, Path],
    message: str,
    output_file: Union[str, Path],
    encoding: str = "UTF-8",
) -> None:
    """
    Writes *output_file* which contains *message* hidden inside the LSB of each
    audio sample byte (supports 8/16/24/32-bit PCM).
    """
    frames, params = _read_frames(input_file)
    frame_bytes = bytearray(frames)

    message_bytes = message.encode(encoding)
    payload_bits = bits_from_bytes(len(message_bytes).to_bytes(4, "big"))
    payload_bits.extend(bits_from_bytes(message_bytes))

    if len(payload_bits) > len(frame_bytes):
        raise ValueError("Audio file is too small for the given message.")

    for i, bit in enumerate(payload_bits):
        frame_bytes[i] = (frame_bytes[i] & ~1) | bit

    _write_frames(output_file, bytes(frame_bytes), params)


def reveal(input_file: Union[str, Path], encoding: str = "UTF-8") -> str:
    """
    Extracts and returns the hidden message from *input_file*.
    """
    frames, _ = _read_frames(input_file)
    bits = [(byte & 1) for byte in frames]

    length_bits = bits[:32]
    msg_len = int.from_bytes(bytes_from_bits(length_bits), "big")

    message_bits = bits[32 : 32 + msg_len * 8]
    message_bytes = bytes_from_bits(message_bits)
    return message_bytes.decode(encoding)