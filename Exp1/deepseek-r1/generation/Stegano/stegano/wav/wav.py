import wave
from ..tools.bititerator import BitIterator

def hide(input_file, message, output_file):
    with wave.open(input_file, 'rb') as wav_in:
        params = wav_in.getparams()
        frames = wav_in.readframes(params.nframes)
    
    sample_width = params.sampwidth
    frame_count = len(frames) // sample_width
    message_bytes = message.encode()
    bit_iterator = BitIterator(message_bytes)
    
    new_frames = bytearray(frames)
    for i in range(0, len(new_frames), sample_width):
        try:
            bit = next(bit_iterator)
        except StopIteration:
            break
        sample = new_frames[i]
        sample = (sample & 0xFE) | bit
        new_frames[i] = sample
    
    with wave.open(output_file, 'wb') as wav_out:
        wav_out.setparams(params)
        wav_out.writeframes(bytes(new_frames))

def reveal(input_file):
    with wave.open(input_file, 'rb') as wav_in:
        frames = wav_in.readframes(wav_in.getnframes())
    
    bits = []
    for byte in frames:
        bits.append(byte & 1)
        if len(bits) % 8 == 0 and bits[-8:] == [0] * 8:
            break
    
    byte_list = []
    for i in range(0, len(bits) - 7, 8):
        byte = bits[i:i+8]
        if byte == [0] * 8:
            break
        byte_value = 0
        for bit in byte:
            byte_value = (byte_value << 1) | bit
        byte_list.append(byte_value)
    
    return bytes(byte_list).decode(errors="ignore").rstrip('\x00')