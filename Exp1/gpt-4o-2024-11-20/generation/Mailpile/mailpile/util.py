import re

def CleanText(text, banned_chars=None):
    """
    Cleans a string by removing banned characters and trimming whitespace.
    """
    if banned_chars:
        text = ''.join(c for c in text if c not in banned_chars)
    return text.strip()

def base36_encode(number):
    """
    Encodes an integer into a base36 string.
    """
    if not isinstance(number, int):
        raise ValueError("Input must be an integer")
    if number < 0:
        raise ValueError("Base36 encoding only supports non-negative integers")

    chars = '0123456789abcdefghijklmnopqrstuvwxyz'
    result = ''
    while number > 0:
        number, remainder = divmod(number, 36)
        result = chars[remainder] + result
    return result or '0'

def base36_decode(string):
    """
    Decodes a base36 string into an integer.
    """
    if not isinstance(string, str):
        raise ValueError("Input must be a string")
    return int(string, 36)