"""
Utility functions for steganography
"""

from PIL import Image


def bytes_to_bits(data):
    """Convert bytes to list of bits"""
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def bits_to_bytes(bits):
    """Convert list of bits to bytes"""
    bytes_list = []
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i+8]
        if len(byte_bits) < 8:
            byte_bits.extend([0] * (8 - len(byte_bits)))
        byte = 0
        for bit in byte_bits:
            byte = (byte << 1) | bit
        bytes_list.append(byte)
    return bytes(bytes_list)


def int_to_bits(value, num_bits):
    """Convert integer to list of bits"""
    bits = []
    for i in range(num_bits - 1, -1, -1):
        bits.append((value >> i) & 1)
    return bits


def bits_to_int(bits):
    """Convert list of bits to integer"""
    value = 0
    for bit in bits:
        value = (value << 1) | bit
    return value


def load_image(image_path):
    """Load image from file"""
    return Image.open(image_path)


def save_image(image, output_path):
    """Save image to file"""
    image.save(output_path)