# mailpile.util
#
# A collection of simplified utility functions for benchmarking.

import re
import string

# --- Base36 Conversion ---
B36_ALPHABET = string.digits + string.ascii_lowercase

def b36_encode(n):
    """Converts an integer to a base36 string."""
    if not isinstance(n, int) or n < 0:
        raise TypeError('number must be a non-negative integer')
    if n == 0:
        return '0'
    
    base36 = []
    while n:
        n, i = divmod(n, 36)
        base36.append(B36_ALPHABET[i])
    
    return ''.join(reversed(base36))

def b36_decode(s):
    """Converts a base36 string to an integer."""
    return int(s, 36)


# --- Text Cleaning ---
# A simplified version of Mailpile's text cleaning logic.
# This regex aims to remove control characters and other non-printable chars,
# but allows common whitespace like newline, tab, and carriage return.
_CLEAN_TEXT_RE = re.compile(
    '[' +
    ''.join([chr(c) for c in range(32)
             if chr(c) not in ('\b', '\t', '\n', '\r')]) +
    ''.join([chr(c) for c in range(127, 160)]) +
    ']'
)

def CleanText(text, bad_char_replacement='?'):
    """
    Cleans a string by removing control characters and invalid bytes.
    """
    if not isinstance(text, str):
        # In a real scenario, we might try to decode from bytes,
        # but for this benchmark, we assume string input.
        return ""
    return _CLEAN_TEXT_RE.sub(bad_char_replacement, text)

# --- Other Helpers ---
def friendly_time(seconds):
    """Converts a duration in seconds to a human-friendly string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"