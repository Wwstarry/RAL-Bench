import wave
import struct
from ..tools import utils, bititerator

def hide(input_file: str, message: str, output_file: str):
    """
    Hides a message in a WAV file using the LSB technique.

    :param input_file: Path to the input WAV file.
    :param message: The message to hide (str).
    :param output_file: Path to save the output WAV file.
    """
    try:
        with wave.open(input_file, 'rb') as wav_in:
            params = wav_in.getparams()
            n_channels, sampwidth, framerate, n_frames, comptype, compname = params
            frames = wav_in.readframes(n_frames)
    except (FileNotFoundError, wave.Error) as e:
        raise IOError(f"Could not read input WAV file: {e}")

    if sampwidth not in [1, 2]:
        raise ValueError("Unsupported sample width. Only 8-bit and 16-bit WAV files are supported.")

    capacity_bits = n_frames * n_channels
    message_bytes = utils.to_bytes(message, "UTF-8")
    
    if len(message_bytes) * 8 > capacity_bits:
        raise ValueError("Message is too large for the WAV file.")

    message_bits = bititerator.bits_from_bytes(message_bytes)
    
    fmt = f"<{n_frames * n_channels}{'h' if sampwidth == 2 else 'B'}"
    samples = list(struct.unpack(fmt, frames))

    bit_iter = iter(message_bits)
    for i in range(len(samples)):
        try:
            bit = next(bit_iter)
            samples[i] = (samples[i] & ~1) | bit
        except StopIteration:
            break

    modified_frames = struct.pack(fmt, *samples)

    try:
        with wave.open(output_file, 'wb') as wav_out:
            wav_out.setparams(params)
            wav_out.writeframes(modified_frames)
    except wave.Error as e:
        raise IOError(f"Could not write output WAV file: {e}")

def reveal(input_file: str) -> str:
    """
    Reveals a message hidden in a WAV file.

    :param input_file: Path to the WAV file.
    :return: The revealed message as a string.
    """
    try:
        with wave.open(input_file, 'rb') as wav_in:
            n_channels = wav_in.getnchannels()
            sampwidth = wav_in.getsampwidth()
            n_frames = wav_in.getnframes()
            frames = wav_in.readframes(n_frames)
    except (FileNotFoundError, wave.Error) as e:
        raise IOError(f"Could not read input WAV file: {e}")

    if sampwidth not in [1, 2]:
        raise ValueError("Unsupported sample width. Only 8-bit and 16-bit WAV files are supported.")

    fmt = f"<{n_frames * n_channels}{'h' if sampwidth == 2 else 'B'}"
    samples = struct.unpack(fmt, frames)

    terminator_bits = utils.get_terminator_bits()
    terminator_len = len(terminator_bits)
    
    extracted_bits = []
    
    for sample in samples:
        lsb = sample & 1
        extracted_bits.append(lsb)

        if len(extracted_bits) >= terminator_len:
            if extracted_bits[-terminator_len:] == terminator_bits:
                break
    else:
        raise ValueError("Terminator not found.")

    message_bits = extracted_bits[:-terminator_len]
    
    byte_array = bytearray()
    for i in range(0, len(message_bits), 8):
        byte_chunk = message_bits[i:i+8]
        if len(byte_chunk) < 8:
            break
        byte = 0
        for bit in byte_chunk:
            byte = (byte << 1) | bit
        byte_array.append(byte)
        
    return byte_array.decode("UTF-8", errors="ignore")