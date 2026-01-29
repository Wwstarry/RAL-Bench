import wave

def hide(input_file, message, output_file):
    with wave.open(input_file, "rb") as wav:
        frames = bytearray(list(wav.readframes(wav.getnframes())))
    binary_message = ''.join(format(ord(char), '08b') for char in message) + '00000000'
    for i, bit in enumerate(binary_message):
        frames[i] = (frames[i] & ~1) | int(bit)
    with wave.open(output_file, "wb") as wav_out:
        wav_out.setparams(wav.getparams())
        wav_out.writeframes(frames)

def reveal(input_file):
    with wave.open(input_file, "rb") as wav:
        frames = bytearray(list(wav.readframes(wav.getnframes())))
    binary_message = ""
    for frame in frames:
        binary_message += str(frame & 1)
    byte_message = [binary_message[i:i+8] for i in range(0, len(binary_message), 8)]
    decoded_message = ''.join(chr(int(byte, 2)) for byte in byte_message if int(byte, 2) != 0)
    return decoded_message