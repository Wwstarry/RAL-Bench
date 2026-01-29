def get_mask_and_val(val, bit):
    """
    Set the LSB of val to bit.
    """
    # Clear LSB then set it
    return (val & ~1) | bit

def str_to_bin(message, encoding="UTF-8"):
    """
    Convert a string to a generator of bits.
    """
    if isinstance(message, str):
        message_bytes = message.encode(encoding)
    else:
        message_bytes = message
        
    for byte in message_bytes:
        for i in range(8):
            yield (byte >> (7 - i)) & 1

def bin_to_str(bits, encoding="UTF-8"):
    """
    Convert a list of bits to a string.
    """
    chars = []
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i+8]
        if len(byte_bits) < 8:
            break
        byte_val = 0
        for b in byte_bits:
            byte_val = (byte_val << 1) | b
        chars.append(byte_val)
    
    try:
        return bytes(chars).decode(encoding)
    except UnicodeDecodeError:
        # Fallback or return raw representation if decode fails
        return bytes(chars).decode(encoding, errors='replace')