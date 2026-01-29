def encode_message(message, encoding="UTF-8"):
    return ''.join(format(ord(char), '08b') for char in message.encode(encoding))

def decode_message(binary_message, encoding="UTF-8"):
    byte_message = [binary_message[i:i+8] for i in range(0, len(binary_message), 8)]
    return ''.join(chr(int(byte, 2)) for byte in byte_message if int(byte, 2) != 0)