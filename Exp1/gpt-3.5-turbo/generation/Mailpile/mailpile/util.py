import re
import string


class CleanText:
    """
    CleanText strips unwanted characters and normalizes text for safe usage.
    """

    def __init__(self, text):
        self.text = text

    def clean(self):
        # Remove control characters except newline and tab
        cleaned = ''.join(ch for ch in self.text if ch in string.printable and ch not in '\x0b\x0c\r')
        # Normalize whitespace to single spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()


def base36_encode(number):
    """
    Convert an integer to a base36 string.
    """
    if not isinstance(number, int):
        raise TypeError('number must be an integer')
    if number < 0:
        raise ValueError('number must be positive')

    alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'
    if number == 0:
        return '0'
    base36 = ''
    while number:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36
    return base36


def base36_decode(s):
    """
    Convert a base36 string to an integer.
    """
    return int(s, 36)


def is_email_address(text):
    """
    Simple helper to check if text looks like an email address.
    """
    if not isinstance(text, str):
        return False
    # Very simple regex for email validation
    return bool(re.match(r'^[^@]+@[^@]+\.[^@]+$', text))


def safe_str(obj):
    """
    Convert an object to a safe string representation.
    """
    try:
        return str(obj)
    except Exception:
        return repr(obj)