import re

def CleanText(text, banned_chars=''):
    """
    Clean text by removing or escaping banned characters.
    
    :param text: The text to be cleaned
    :param banned_chars: A string of characters to remove
    :return: Cleaned text
    """
    if not isinstance(text, str):
        text = str(text)
    if banned_chars:
        # Remove banned characters
        rx = '[' + re.escape(banned_chars) + ']+'
        text = re.sub(rx, '', text)
    return text

def int_to_base36(num):
    """
    Convert an integer to a base36 (0-9, a-z) string.
    
    :param num: The integer to convert
    :return: Base36 string
    """
    digits = '0123456789abcdefghijklmnopqrstuvwxyz'
    if num < 0:
        sign = '-'
        num = -num
    else:
        sign = ''
    result = ''
    if num == 0:
        return '0'
    while num:
        num, rem = divmod(num, 36)
        result = digits[rem] + result
    return sign + result

def base36_to_int(base36):
    """
    Convert a base36 (0-9, a-z) string to an integer.
    
    :param base36: The base36 string to convert
    :return: Integer value
    """
    return int(base36, 36)

def friendly_number(num):
    """
    Return a friendly string representation of a number (e.g. 1,234).
    """
    return "{:,}".format(num)