# stegano/wav/wav.py
import wave
from stegano.tools import utils

def hide(input_file, message, output_file, encoding="UTF-8"):
    """
    Hides a message in the LSB of audio samples in a WAV file.
    """
    try:
        with wave.open(input_file, 'rb') as wav_in:
            params = wav_in.getparams()
            nframes = wav_in.getnframes()
            frames = wav_in.readframes(nframes)
    except wave.Error as e:
        raise IOError(f"Could not read input WAV file: {input_file}") from e
    except FileNotFoundError:
        raise

    if not frames:
        raise ValueError("Input WAV file is empty.")

    message_bits = list(utils.get_bit_generator(message, encoding))
    
    if len(message_bits) > len(frames):
        raise ValueError("Message is too long to be hidden in this WAV file.")

    # Use a bytearray for mutable sequence of bytes
    frames_ba = bytearray(frames)

    for i, bit in enumerate(message_bits):
        frames_ba[i] = (frames_ba[i] & 0xFE) | bit

    try:
        with wave.open(output_file, 'wb') as wav_out:
            wav_out.setparams(params)
            wav_out.writeframes(bytes(frames_ba))
    except wave.Error as e:
        raise IOError(f"Could not write output WAV file: {output_file}") from e


def reveal(input_file, encoding="UTF-8"):
    """
    Reveals a message hidden in the LSB of audio samples in a WAV file.
    """
    try:
        with wave.open(input_file, 'rb') as wav_in:
            nframes = wav_in.getnframes()
            frames = wav_in.readframes(nframes)
    except wave.Error as e:
        raise IOError(f"Could not read input WAV file: {input_file}") from e
    except FileNotFoundError:
        raise

    if not frames:
        raise ValueError("Input WAV file is empty.")

    extracted_bits = []
    delimiter_found = False

    for byte in frames:
        extracted_bits.append(byte & 1)
        if len(extracted_bits) >= 8 and extracted_bits[-8:] == utils.DELIMITER:
            delimiter_found = True
            break
    
    if not delimiter_found:
        raise ValueError("No hidden message found or delimiter is missing.")

    message_bits = extracted_bits[:-8]

    try:
        message_bytes = utils.bits_to_bytes(message_bits)
        return message_bytes.decode(encoding)
    except Exception as e:
        raise ValueError("Failed to decode message. Data may be corrupt or encoding incorrect.") from e