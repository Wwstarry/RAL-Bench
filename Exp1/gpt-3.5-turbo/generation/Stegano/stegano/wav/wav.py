import wave
import contextlib


def hide(input_file: str, message: str, output_file: str, **kwargs) -> None:
    """
    Hide a message in the least significant bits of PCM audio samples in a WAV file.

    :param input_file: path to input WAV file (PCM)
    :param message: message string to hide
    :param output_file: path to output WAV file with hidden message
    :param kwargs: ignored for compatibility
    """
    with contextlib.closing(wave.open(input_file, 'rb')) as wav_in:
        params = wav_in.getparams()
        n_frames = wav_in.getnframes()
        frames = bytearray(wav_in.readframes(n_frames))

    # Convert message to bits and append null byte
    message_bytes = message.encode("UTF-8") + b'\x00'
    bits = []
    for byte in message_bytes:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)

    max_bits = len(frames)
    if len(bits) > max_bits:
        raise ValueError("Message too long to hide in WAV file")

    # Modify LSB of each byte in frames
    for i, bit in enumerate(bits):
        frames[i] = (frames[i] & 0xFE) | bit

    with contextlib.closing(wave.open(output_file, 'wb')) as wav_out:
        wav_out.setparams(params)
        wav_out.writeframes(frames)


def reveal(input_file: str, **kwargs) -> str:
    """
    Reveal a hidden message from the least significant bits of PCM audio samples in a WAV file.

    :param input_file: path to input WAV file
    :param kwargs: ignored for compatibility
    :return: revealed message string
    """
    with contextlib.closing(wave.open(input_file, 'rb')) as wav_in:
        n_frames = wav_in.getnframes()
        frames = wav_in.readframes(n_frames)

    bits = []
    for byte in frames:
        bits.append(byte & 1)

    bytes_out = bytearray()
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i + 8]
        if len(byte_bits) < 8:
            break
        byte = 0
        for bit in byte_bits:
            byte = (byte << 1) | bit
        if byte == 0:
            break
        bytes_out.append(byte)

    return bytes_out.decode("UTF-8", errors='replace')