"""
Simple WAV LSB steganography.

Only supports 16-bit PCM (uncompressed) WAV files for demonstration.
"""
import struct


def hide(input_file, message, output_file, **kwargs):
    """
    Hide a message string in a 16-bit PCM WAV file, in the LSB of each sample.
    Writes a new file to output_file.
    :param input_file: path to the cover WAV file.
    :param message: the text message to embed.
    :param output_file: output path for the modified WAV.
    :param kwargs: additional arguments (ignored for signature compatibility).
    """
    with open(input_file, "rb") as f_in:
        wav_data = f_in.read()

    # Parse header
    if not wav_data.startswith(b"RIFF") or not wav_data[8:12] == b"WAVE":
        raise ValueError("Not a valid WAV file (missing RIFF/WAVE).")

    # Search for 'fmt ' chunk, 'data' chunk
    # We'll do a simple pass to find them
    offset = 12  # skip RIFF header
    fmt_offset = None
    data_offset = None
    data_size = None

    while offset < len(wav_data):
        chunk_id = wav_data[offset:offset+4]
        chunk_size = struct.unpack("<I", wav_data[offset+4:offset+8])[0]
        if chunk_id == b"fmt ":
            fmt_offset = offset
        elif chunk_id == b"data":
            data_offset = offset + 8
            data_size = chunk_size
            break
        offset += 8 + chunk_size

    if fmt_offset is None or data_offset is None or data_size is None:
        raise ValueError("Could not find required chunks in WAV file.")

    # Check if it's 16-bit PCM
    # Format code is at fmt_offset+8 (2 bytes)
    audio_format, num_channels, sample_rate, byte_rate, block_align, bits_per_sample = struct.unpack(
        "<HHIIHH", wav_data[fmt_offset+8:fmt_offset+8+16]
    )
    if audio_format != 1 or bits_per_sample != 16:
        raise ValueError("Only 16-bit PCM WAV is supported by this simple steganography.")

    # Get the sample data
    audio_data = bytearray(wav_data[data_offset:data_offset+data_size])

    # Convert message to bits
    # We'll store len(message) as 4 bytes + message
    message_bytes = message.encode("utf-8")
    msg_len = len(message_bytes)
    length_bytes = struct.pack("<I", msg_len)
    full_payload = length_bytes + message_bytes

    # Each sample is 2 bytes => we can store 1 bit per sample (LSB).
    num_samples = len(audio_data) // 2

    total_bits = len(full_payload) * 8
    if total_bits > num_samples:
        raise ValueError("Message is too large to fit in the given WAV.")

    # Hide bits
    bit_idx = 0
    for i in range(len(full_payload)):
        byte_val = full_payload[i]
        for b in range(8):
            bit = (byte_val >> b) & 1
            # replace LSB of sample
            sample_idx = bit_idx
            sample_bytes = audio_data[sample_idx*2:(sample_idx*2)+2]
            sample_val = struct.unpack("<h", sample_bytes)[0]
            sample_val = (sample_val & 0xFFFE) | bit
            audio_data[sample_idx*2:(sample_idx*2)+2] = struct.pack("<h", sample_val)
            bit_idx += 1

    # Construct the new WAV
    new_wav = bytearray(wav_data)
    new_wav[data_offset:data_offset+data_size] = audio_data

    with open(output_file, "wb") as f_out:
        f_out.write(new_wav)


def reveal(input_file, **kwargs) -> str:
    """
    Reveal a hidden message in a 16-bit PCM WAV file.
    :param input_file: path to the WAV file containing hidden text.
    :param kwargs: additional args (ignored for signature compatibility).
    :return: The hidden text.
    """
    with open(input_file, "rb") as f_in:
        wav_data = f_in.read()

    if not wav_data.startswith(b"RIFF") or not wav_data[8:12] == b"WAVE":
        raise ValueError("Not a valid WAV file (missing RIFF/WAVE).")

    offset = 12
    fmt_offset = None
    data_offset = None
    data_size = None

    while offset < len(wav_data):
        chunk_id = wav_data[offset:offset+4]
        chunk_size = struct.unpack("<I", wav_data[offset+4:offset+8])[0]
        if chunk_id == b"fmt ":
            fmt_offset = offset
        elif chunk_id == b"data":
            data_offset = offset + 8
            data_size = chunk_size
            break
        offset += 8 + chunk_size

    if fmt_offset is None or data_offset is None or data_size is None:
        raise ValueError("Could not find required chunks in WAV file.")

    # read data
    audio_data = wav_data[data_offset:data_offset+data_size]
    num_samples = len(audio_data) // 2

    # We first read 4 bytes = message length
    # 4 bytes * 8 bits = 32 bits
    needed_bits_for_len = 32
    if num_samples < needed_bits_for_len:
        return ""

    # gather bits
    bit_idx = 0
    length_bits = []
    for _ in range(needed_bits_for_len):
        sample_bytes = audio_data[bit_idx*2:(bit_idx*2)+2]
        sample_val = struct.unpack("<h", sample_bytes)[0]
        length_bits.append(sample_val & 1)
        bit_idx += 1

    # convert bits to length
    length_val = 0
    for i in range(32):
        length_val |= (length_bits[i] << i)
    msg_length = length_val

    total_bits_needed = msg_length * 8
    if bit_idx + total_bits_needed > num_samples:
        return ""

    msg_bits = []
    for _ in range(total_bits_needed):
        sample_bytes = audio_data[bit_idx*2:(bit_idx*2)+2]
        sample_val = struct.unpack("<h", sample_bytes)[0]
        msg_bits.append(sample_val & 1)
        bit_idx += 1

    # reconstruct bytes
    msg_bytes = bytearray()
    for i in range(0, len(msg_bits), 8):
        byte_val = 0
        for b in range(8):
            byte_val |= (msg_bits[i+b] << b)
        msg_bytes.append(byte_val)

    return msg_bytes.decode("utf-8")