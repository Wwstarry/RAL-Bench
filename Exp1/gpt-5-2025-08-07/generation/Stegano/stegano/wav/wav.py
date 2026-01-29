import wave
from typing import List, Tuple, Union
from ..tools.utils import message_to_bytes, int_to_bits_be, bytes_to_bits, bits_to_int_be, bits_to_bytes

def _frames_to_samples(frames: bytes, sampwidth: int) -> List[int]:
    """
    Convert raw PCM frames to a list of sample integers.
    Supports 8-bit (unsigned) and 16-bit (signed little-endian) PCM.
    """
    samples: List[int] = []
    if sampwidth == 1:
        # Bytes are unsigned 8-bit
        samples = list(frames)
    elif sampwidth == 2:
        # 16-bit little-endian signed
        if len(frames) % 2 != 0:
            raise ValueError("Corrupted 16-bit PCM data length.")
        for i in range(0, len(frames), 2):
            val = int.from_bytes(frames[i:i+2], byteorder="little", signed=True)
            samples.append(val)
    else:
        raise ValueError("Unsupported sample width: {}".format(sampwidth))
    return samples

def _samples_to_frames(samples: List[int], sampwidth: int) -> bytes:
    """
    Convert list of samples back to raw PCM frames.
    """
    if sampwidth == 1:
        return bytes([s & 0xFF for s in samples])
    elif sampwidth == 2:
        out = bytearray()
        for s in samples:
            out.extend(int(s).to_bytes(2, byteorder="little", signed=True))
        return bytes(out)
    else:
        raise ValueError("Unsupported sample width: {}".format(sampwidth))

def hide(input_file, message: Union[str, bytes], output_file, encoding: str = "UTF-8") -> None:
    """
    Hide a message inside a WAV PCM file using LSB of samples.
    Writes a new file at output_file with the same parameters as input_file.
    Stores a 32-bit big-endian length prefix followed by message bytes.
    """
    with wave.open(input_file, "rb") as wf:
        params = wf.getparams()
        n_channels = params.nchannels
        sampwidth = params.sampwidth
        n_frames = params.nframes
        frames = wf.readframes(n_frames)
    samples = _frames_to_samples(frames, sampwidth)
    total_samples = len(samples)

    msg_bytes = message_to_bytes(message, encoding)
    payload_bits = bytes_to_bits(msg_bytes)
    length_bits = int_to_bits_be(len(msg_bytes), 32)
    full_bits = length_bits + payload_bits

    if len(full_bits) > total_samples:
        raise ValueError("Not enough capacity in WAV samples to hide the message.")

    mutable_samples = list(samples)
    for i, bit in enumerate(full_bits):
        mutable_samples[i] = (mutable_samples[i] & ~1) | (bit & 1)

    new_frames = _samples_to_frames(mutable_samples, sampwidth)
    with wave.open(output_file, "wb") as wf_out:
        wf_out.setparams(params)
        wf_out.writeframes(new_frames)

def reveal(input_file, encoding: str = "UTF-8") -> str:
    """
    Reveal a message from a WAV PCM file using the LSBs of samples.
    Expects a 32-bit big-endian length header.
    """
    with wave.open(input_file, "rb") as wf:
        params = wf.getparams()
        sampwidth = params.sampwidth
        n_frames = params.nframes
        frames = wf.readframes(n_frames)
    samples = _frames_to_samples(frames, sampwidth)
    if len(samples) < 32:
        return ""

    length_bits: List[int] = []
    for i in range(32):
        length_bits.append(samples[i] & 1)
    msg_len = bits_to_int_be(length_bits)

    payload_bits_count = msg_len * 8
    if 32 + payload_bits_count > len(samples):
        raise ValueError("Not enough data to reveal the message from WAV samples.")
    payload_bits: List[int] = []
    for i in range(32, 32 + payload_bits_count):
        payload_bits.append(samples[i] & 1)
    msg_bytes = bits_to_bytes(payload_bits)
    try:
        return msg_bytes.decode(encoding, errors="strict")
    except Exception:
        return msg_bytes.decode(encoding, errors="replace")