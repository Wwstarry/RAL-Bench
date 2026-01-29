from .bititerator import bits_from_bytes

# The default message terminator, compatible with the reference library.
MESSAGE_TERMINATOR = b'\x00\x00\x00\x00\x00\x00'

def to_bytes(message, encoding="UTF-8") -> bytes:
    """
    Converts a string or bytes to bytes with a terminator appended.
    """
    if isinstance(message, str):
        encoded_message = message.encode(encoding)
    elif isinstance(message, bytes):
        encoded_message = message
    else:
        raise TypeError("Message must be a string or bytes.")
    
    return encoded_message + MESSAGE_TERMINATOR

def get_terminator_bits() -> list:
    """
    Returns the bits of the message terminator as a list of ints.
    """
    return list(bits_from_bytes(MESSAGE_TERMINATOR))