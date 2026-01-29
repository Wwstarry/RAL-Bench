import wave
import struct

def hide(input_file, message, output_file, **kwargs):
    if isinstance(message, str):
        message_bytes = message.encode("UTF-8")
    else:
        message_bytes = message
    message_bytes += b'\x00'
    with wave.open(input_file, "rb") as wav_in:
        params = wav_in.getparams()
        frames = wav_in.readframes(params.nframes)
    sample_width = params.sampwidth
    n_channels = params.nchannels
    n_frames = params.nframes
    total_samples = n_frames * n_channels
    if sample_width == 1:
        fmt = "{}B".format(total_samples)
    elif sample_width == 2:
        fmt = "{}h".format(total_samples)
    else:
        raise ValueError("Unsupported sample width")
    samples = list(struct.unpack(fmt, frames))
    bits = []
    for byte in message_bytes:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    if len(bits) > len(samples):
        raise ValueError("Message too large to hide in audio")
    for i, bit in enumerate(bits):
        samples[i] = (samples[i] & ~1) | bit
    packed = struct.pack(fmt, *samples)
    with wave.open(output_file, "wb") as wav_out:
        wav_out.setparams(params)
        wav_out.writeframes(packed)

def reveal(input_file, **kwargs):
    with wave.open(input_file, "rb") as wav_in:
        params = wav_in.getparams()
        frames = wav_in.readframes(params.nframes)
    sample_width = params.sampwidth
    n_channels = params.nchannels
    n_frames = params.nframes
    total_samples = n_frames * n_channels
    if sample_width == 1:
        fmt = "{}B".format(total_samples)
    elif sample_width == 2:
        fmt = "{}h".format(total_samples)
    else:
        raise ValueError("Unsupported sample width")
    samples = list(struct.unpack(fmt, frames))
    bits = []
    for sample in samples:
        bits.append(sample & 1)
        if len(bits) % 8 == 0 and bits[-8:] == [0]*8:
            break
    bytes_out = bytearray()
    byte = 0
    count = 0
    for bit in bits:
        byte = (byte << 1) | bit
        count += 1
        if count == 8:
            if byte == 0:
                break
            bytes_out.append(byte)
            byte = 0
            count = 0
    return bytes_out.decode("UTF-8")